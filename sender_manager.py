import json
import os
import time
import threading
import sys
from datetime import datetime
from typing import List, Dict, Optional
from resend_provider import ResendProvider
from proxy_handler import ProxyHandler
from template_manager import TemplateManager
from variable_parser import VariableParser

# 獲取程式所在目錄（支持打包後的 exe）
def get_app_dir():
    if getattr(sys, 'frozen', False):
        # 打包後的 exe
        return os.path.dirname(sys.executable)
    else:
        # 開發環境
        return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_dir()

class SenderManager:
    def __init__(self, data_dir: str = "data", logs_dir: str = "logs"):
        self.data_dir = os.path.join(APP_DIR, data_dir)
        self.logs_dir = os.path.join(APP_DIR, logs_dir)
        self.template_manager = TemplateManager(os.path.join(APP_DIR, "templates"))
        self.proxy_handler = ProxyHandler()
        
        self.running = False
        self.paused = False
        self.thread = None
        
        # 統計數據
        self.total_sent = 0
        self.total_success = 0
        self.total_failed = 0
        self.start_time = None
        
        # 回調函數
        self.on_progress = None
        self.on_log = None
        self.on_complete = None
        
        # 確保日誌目錄存在
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        
        if not os.path.exists(os.path.join(self.data_dir, "send_logs")):
            os.makedirs(os.path.join(self.data_dir, "send_logs"))

    def load_apis(self) -> List[Dict]:
        """加載 API 配置"""
        try:
            with open(os.path.join(self.data_dir, "apis.json"), 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [data[key] for key in data]
        except Exception as e:
            self._log(f"加載 API 配置失敗: {e}")
            return []

    def _log(self, message: str):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        if self.on_log:
            self.on_log(log_message)

    def _save_send_log(self, session_id: str, logs: List[Dict]):
        """保存發送日誌"""
        try:
            log_dir = os.path.join(self.data_dir, "send_logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            log_file = os.path.join(log_dir, f"session_{session_id}.json")
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"保存日誌失敗: {e}")

    def start_sending(self, params: Dict):
        """開始發送郵件"""
        if self.running:
            self._log("發送任務正在運行中")
            return False
        
        self.running = True
        self.paused = False
        self.total_sent = 0
        self.total_success = 0
        self.total_failed = 0
        self.start_time = datetime.now()
        
        self.thread = threading.Thread(target=self._send_worker, args=(params,))
        self.thread.daemon = True
        self.thread.start()
        
        self._log("發送任務已啟動")
        return True

    def pause_sending(self):
        """暫停發送"""
        if self.running and not self.paused:
            self.paused = True
            self._log("發送任務已暫停")

    def resume_sending(self):
        """恢復發送"""
        if self.running and self.paused:
            self.paused = False
            self._log("發送任務已恢復")

    def stop_sending(self):
        """停止發送"""
        if self.running:
            self.running = False
            self.paused = False
            self.proxy_handler.cleanup()
            self._log("發送任務已停止")
            
            if self.on_complete:
                self.on_complete()

    def _send_worker(self, params: Dict):
        """發送工作線程"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        send_logs = []
        
        # 解析參數
        recipients = [line.strip() for line in params.get('recipients', '').split('\n') if line.strip()]
        url_pool = params.get('url_pool', '').strip().split('\n') if params.get('url_pool') else []
        url_pool_enabled = params.get('url_pool_enabled', False)
        subject = params.get('subject', '')
        body = params.get('body', '')
        is_html = params.get('is_html', False)
        batch_size = params.get('batch_size', 1)
        max_concurrent = params.get('max_concurrent', 1)
        batch_interval = params.get('batch_interval', 1)
        same_domain_delay = params.get('same_domain_delay', 1)
        
        # 加載 API 和模板
        apis = self.load_apis()
        templates = self.template_manager.get_templates()
        
        if not apis:
            self._log("錯誤: 沒有可用的 API 配置")
            self.stop_sending()
            return
        
        if not recipients:
            self._log("錯誤: 沒有收件人")
            self.stop_sending()
            return
        
        api_index = 0
        template_index = 0
        url_index = 0
        
        # 域名追蹤（用於同域延遲）
        domain_last_sent = {}
        
        # 並發控制
        import concurrent.futures
        
        def send_single_email(recipient):
            """發送單封郵件"""
            if not self.running:
                return None
            
            while self.paused:
                if not self.running:
                    return None
                time.sleep(0.5)
            
            if not self.running:
                return None
            
            nonlocal api_index, template_index, url_index
            
            # 同域延遲檢查
            domain = recipient.split('@')[1] if '@' in recipient else recipient
            if domain in domain_last_sent:
                elapsed = (datetime.now() - domain_last_sent[domain]).total_seconds()
                if elapsed < same_domain_delay:
                    wait_time = same_domain_delay - elapsed
                    self._log(f"同域延遲: {domain} 等待 {wait_time:.1f} 秒")
                    time.sleep(wait_time)
            
            # 選擇 API
            api = apis[api_index % len(apis)]
            api_index += 1
            
            # 選擇模板
            template = self.template_manager.get_next_template(templates, template_index)
            if template:
                template_content = template.get('content', body)
                template_is_html = template.get('is_html', is_html)
            else:
                template_content = body
                template_is_html = is_html
            template_index += 1
            
            # 選擇 URL
            link = ""
            if url_pool_enabled and url_pool:
                link = url_pool[url_index % len(url_pool)]
                url_index += 1
            
            # 構建上下文
            context = {
                "sender": api.get('from_name', api.get('from_email', '')),
                "recipient": recipient,
                "link": link
            }
            
            # 替換變數
            final_subject = VariableParser.parse(subject, context)
            final_body = VariableParser.parse(template_content, context)
            
            # 設置代理
            proxies = self.proxy_handler.setup_proxy(api)
            
            # 發送郵件
            try:
                provider = ResendProvider(api['api_key'], proxies=proxies)
                
                payload = {
                    "from": f"{api.get('from_name', '')} <{api['from_email']}>" if api.get('from_name') else api['from_email'],
                    "to": [recipient],
                    "subject": final_subject
                }
                
                if template_is_html:
                    payload["html"] = final_body
                else:
                    payload["text"] = final_body
                
                status_code, response, response_text = provider.send_one(payload)
                
                log_entry = {
                    "recipient": recipient,
                    "api": api['name'],
                    "timestamp": datetime.now().isoformat()
                }
                
                if status_code in [200, 202]:
                    log_entry["status"] = "success"
                    self._log(f"✓ 成功: {recipient}")
                else:
                    log_entry["status"] = "failed"
                    log_entry["error"] = response_text if response_text else str(response)
                    self._log(f"✗ 失敗: {recipient} - {log_entry['error']}")
                
                # 清理代理
                self.proxy_handler.cleanup()
                
                # 記錄發送時間
                domain_last_sent[domain] = datetime.now()
                
                return log_entry
                
            except Exception as e:
                log_entry = {
                    "recipient": recipient,
                    "status": "error",
                    "api": api['name'],
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self._log(f"✗ 異常: {recipient} - {str(e)}")
                self.proxy_handler.cleanup()
                return log_entry
        
        # 批次處理
        for i in range(0, len(recipients), batch_size):
            if not self.running:
                break
            
            batch = recipients[i:i + batch_size]
            
            # 並發發送
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures = [executor.submit(send_single_email, recipient) for recipient in batch]
                
                for future in concurrent.futures.as_completed(futures):
                    if not self.running:
                        break
                    
                    result = future.result()
                    if result:
                        self.total_sent += 1
                        if result["status"] == "success":
                            self.total_success += 1
                        else:
                            self.total_failed += 1
                        send_logs.append(result)
                        
                        # 更新進度
                        if self.on_progress:
                            progress = {
                                "total": len(recipients),
                                "sent": self.total_sent,
                                "success": self.total_success,
                                "failed": self.total_failed,
                                "rate": self._calculate_rate()
                            }
                            self.on_progress(progress)
            
            # 批次間隔
            if i + batch_size < len(recipients) and self.running:
                self._log(f"批次完成，等待 {batch_interval} 秒")
                time.sleep(batch_interval)
            
            # 同域延遲檢查
            domain = recipient.split('@')[1] if '@' in recipient else recipient
            if domain in domain_last_sent:
                elapsed = (datetime.now() - domain_last_sent[domain]).total_seconds()
                if elapsed < same_domain_delay:
                    wait_time = same_domain_delay - elapsed
                    self._log(f"同域延遲: {domain} 等待 {wait_time:.1f} 秒")
                    time.sleep(wait_time)
            
            # 選擇 API
            api = apis[api_index % len(apis)]
            api_index += 1
            
            # 選擇模板
            template = self.template_manager.get_next_template(templates, template_index)
            if template:
                template_content = template.get('content', body)
                template_is_html = template.get('is_html', is_html)
            else:
                template_content = body
                template_is_html = is_html
            template_index += 1
            
            # 選擇 URL
            link = ""
            if url_pool_enabled and url_pool:
                link = url_pool[url_index % len(url_pool)]
                url_index += 1
            
            # 構建上下文
            context = {
                "sender": api.get('from_name', api.get('from_email', '')),
                "recipient": recipient,
                "link": link
            }
            
            # 替換變數
            final_subject = VariableParser.parse(subject, context)
            final_body = VariableParser.parse(template_content, context)
            
            # 設置代理
            proxies = self.proxy_handler.setup_proxy(api)
            
            # 發送郵件
            try:
                provider = ResendProvider(api['api_key'], proxies=proxies)
                
                payload = {
                    "from": f"{api.get('from_name', '')} <{api['from_email']}>" if api.get('from_name') else api['from_email'],
                    "to": [recipient],
                    "subject": final_subject
                }
                
                if template_is_html:
                    payload["html"] = final_body
                else:
                    payload["text"] = final_body
                
                status_code, response, response_text = provider.send_one(payload)
                
                self.total_sent += 1
                
                if status_code in [200, 202]:
                    self.total_success += 1
                    self._log(f"✓ 成功: {recipient}")
                    send_logs.append({
                        "recipient": recipient,
                        "status": "success",
                        "api": api['name'],
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    self.total_failed += 1
                    error_msg = response_text if response_text else str(response)
                    self._log(f"✗ 失敗: {recipient} - {error_msg}")
                    send_logs.append({
                        "recipient": recipient,
                        "status": "failed",
                        "api": api['name'],
                        "error": error_msg,
                        "timestamp": datetime.now().isoformat()
                    })
                
            except Exception as e:
                self.total_sent += 1
                self.total_failed += 1
                self._log(f"✗ 異常: {recipient} - {str(e)}")
                send_logs.append({
                    "recipient": recipient,
                    "status": "error",
                    "api": api['name'],
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            # 清理代理
            self.proxy_handler.cleanup()
            
            # 更新進度
            if self.on_progress:
                progress = {
                    "total": len(recipients),
                    "sent": self.total_sent,
                    "success": self.total_success,
                    "failed": self.total_failed,
                    "rate": self._calculate_rate()
                }
                self.on_progress(progress)
            
            # 批次間隔
            if batch_size > 1 and self.total_sent % batch_size == 0:
                self._log(f"批次完成，等待 {batch_interval} 秒")
                time.sleep(batch_interval)
            
            # 記錄發送時間
            domain_last_sent[domain] = datetime.now()
        
        # 保存日誌
        self._save_send_log(session_id, send_logs)
        self._log(f"發送任務完成 - 成功: {self.total_success}, 失敗: {self.total_failed}")
        
        self.stop_sending()

    def _calculate_rate(self) -> float:
        """計算發送速率（封/秒）"""
        if not self.start_time or self.total_sent == 0:
            return 0.0
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed == 0:
            return 0.0
        
        return round(self.total_sent / elapsed, 2)