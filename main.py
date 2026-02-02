import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QCheckBox, QSpinBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
    QComboBox, QProgressBar, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
import requests
from sender_manager import SenderManager
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

class ApiConfigDialog(QDialog):
    def __init__(self, parent=None, api_data=None):
        super().__init__(parent)
        self.setWindowTitle("API 配置")
        self.setMinimumWidth(500)
        self.api_data = api_data or {}
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()
        
        self.name_input = QLineEdit(self.api_data.get('name', ''))
        self.api_key_input = QLineEdit(self.api_data.get('api_key', ''))
        self.from_email_input = QLineEdit(self.api_data.get('from_email', ''))
        self.from_name_input = QLineEdit(self.api_data.get('from_name', ''))
        
        layout.addRow("名稱:", self.name_input)
        layout.addRow("API Key:", self.api_key_input)
        layout.addRow("發件郵箱:", self.from_email_input)
        layout.addRow("發件人名稱:", self.from_name_input)
        
        # SSH 設定
        ssh_group = QGroupBox("SSH 設定")
        ssh_layout = QFormLayout()
        
        self.ssh_enabled = QCheckBox("啟用 SSH")
        self.ssh_enabled.setChecked(self.api_data.get('ssh_enabled', False))
        
        self.ssh_host_input = QLineEdit(self.api_data.get('ssh_host', ''))
        self.ssh_port_input = QSpinBox()
        self.ssh_port_input.setRange(1, 65535)
        self.ssh_port_input.setValue(self.api_data.get('ssh_port', 22))
        
        self.ssh_username_input = QLineEdit(self.api_data.get('ssh_username', ''))
        self.ssh_password_input = QLineEdit(self.api_data.get('ssh_password', ''))
        self.ssh_password_input.setEchoMode(QLineEdit.Password)
        
        self.ssh_key_file_input = QLineEdit(self.api_data.get('ssh_key_file', ''))
        ssh_key_btn = QPushButton("選擇...")
        ssh_key_btn.clicked.connect(self.select_ssh_key_file)
        
        self.ssh_local_port_input = QSpinBox()
        self.ssh_local_port_input.setRange(1024, 65535)
        self.ssh_local_port_input.setValue(self.api_data.get('ssh_local_port', 10800))
        
        ssh_layout.addRow(self.ssh_enabled)
        ssh_layout.addRow("主機:", self.ssh_host_input)
        ssh_layout.addRow("端口:", self.ssh_port_input)
        ssh_layout.addRow("用戶名:", self.ssh_username_input)
        ssh_layout.addRow("密碼:", self.ssh_password_input)
        ssh_layout.addRow("密鑰文件:", self.ssh_key_file_input)
        ssh_layout.addRow(ssh_key_btn)
        ssh_layout.addRow("本地端口:", self.ssh_local_port_input)
        
        ssh_group.setLayout(ssh_layout)
        
        # Proxy 設定
        proxy_group = QGroupBox("Proxy 設定")
        proxy_layout = QFormLayout()
        
        self.proxy_enabled = QCheckBox("啟用 Proxy")
        self.proxy_enabled.setChecked(self.api_data.get('proxy_enabled', False))
        
        self.proxy_type_input = QComboBox()
        self.proxy_type_input.addItems(["http", "https", "socks5"])
        self.proxy_type_input.setCurrentText(self.api_data.get('proxy_type', 'socks5'))
        
        self.proxy_host_input = QLineEdit(self.api_data.get('proxy_host', ''))
        self.proxy_port_input = QSpinBox()
        self.proxy_port_input.setRange(1, 65535)
        self.proxy_port_input.setValue(self.api_data.get('proxy_port', 10000))
        
        self.proxy_username_input = QLineEdit(self.api_data.get('proxy_username', ''))
        self.proxy_password_input = QLineEdit(self.api_data.get('proxy_password', ''))
        self.proxy_password_input.setEchoMode(QLineEdit.Password)
        
        self.proxy_full_url_input = QLineEdit(self.api_data.get('proxy_full_url', ''))
        
        proxy_layout.addRow(self.proxy_enabled)
        proxy_layout.addRow("類型:", self.proxy_type_input)
        proxy_layout.addRow("主機:", self.proxy_host_input)
        proxy_layout.addRow("端口:", self.proxy_port_input)
        proxy_layout.addRow("用戶名:", self.proxy_username_input)
        proxy_layout.addRow("密碼:", self.proxy_password_input)
        proxy_layout.addRow("完整 URL:", self.proxy_full_url_input)
        
        proxy_group.setLayout(proxy_layout)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(ssh_group)
        main_layout.addWidget(proxy_group)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        main_layout.addWidget(buttons)
        self.setLayout(main_layout)

    def select_ssh_key_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "選擇 SSH 密鑰文件", "", "所有文件 (*)"
        )
        if filename:
            self.ssh_key_file_input.setText(filename)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "api_key": self.api_key_input.text(),
            "from_email": self.from_email_input.text(),
            "from_name": self.from_name_input.text(),
            "ssh_enabled": self.ssh_enabled.isChecked(),
            "ssh_host": self.ssh_host_input.text(),
            "ssh_port": self.ssh_port_input.value(),
            "ssh_username": self.ssh_username_input.text(),
            "ssh_password": self.ssh_password_input.text(),
            "ssh_key_file": self.ssh_key_file_input.text(),
            "ssh_local_port": self.ssh_local_port_input.value(),
            "proxy_enabled": self.proxy_enabled.isChecked(),
            "proxy_type": self.proxy_type_input.currentText(),
            "proxy_host": self.proxy_host_input.text(),
            "proxy_port": self.proxy_port_input.value(),
            "proxy_username": self.proxy_username_input.text(),
            "proxy_password": self.proxy_password_input.text(),
            "proxy_full_url": self.proxy_full_url_input.text()
        }


class TemplateDialog(QDialog):
    def __init__(self, parent=None, template_data=None):
        super().__init__(parent)
        self.setWindowTitle("模板管理")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.template_data = template_data or {}
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()
        
        self.name_input = QLineEdit(self.template_data.get('name', ''))
        self.subject_input = QLineEdit(self.template_data.get('subject', ''))
        
        self.content_input = QTextEdit()
        self.content_input.setPlainText(self.template_data.get('content', ''))
        self.content_input.setMinimumHeight(300)
        
        self.is_html = QCheckBox("HTML 格式")
        self.is_html.setChecked(self.template_data.get('is_html', False))
        
        layout.addRow("模板名稱:", self.name_input)
        layout.addRow("主題:", self.subject_input)
        layout.addRow(self.is_html)
        layout.addRow("內容:", self.content_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(buttons)
        self.setLayout(main_layout)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "subject": self.subject_input.text(),
            "content": self.content_input.toPlainText(),
            "is_html": self.is_html.isChecked()
        }


class AiTemplateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 模板生成")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("OpenRouter API Key")
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("輸入郵件主題和要求...")
        self.prompt_input.setMinimumHeight(100)
        
        self.count_input = QSpinBox()
        self.count_input.setRange(1, 10)
        self.count_input.setValue(1)
        
        layout.addRow("API Key:", self.api_key_input)
        layout.addRow("提示詞:", self.prompt_input)
        layout.addRow("生成數量:", self.count_input)
        
        self.generate_btn = QPushButton("生成")
        self.generate_btn.clicked.connect(self.generate_templates)
        
        self.progress_label = QLabel("")
        
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(self.generate_btn)
        main_layout.addWidget(self.progress_label)
        main_layout.addWidget(buttons)
        self.setLayout(main_layout)

    def generate_templates(self):
        api_key = self.api_key_input.text().strip()
        prompt = self.prompt_input.toPlainText().strip()
        count = self.count_input.value()
        
        if not api_key:
            QMessageBox.warning(self, "警告", "請輸入 API Key")
            return
        
        if not prompt:
            QMessageBox.warning(self, "警告", "請輸入提示詞")
            return
        
        try:
            self.progress_label.setText("正在生成...")
            QApplication.processEvents()
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一個郵件模板生成助手。請生成郵件模板，返回 JSON 格式，包含 name, subject, content, is_html 欄位。content 應該支持變數替換：{{发件人}}, {{收件人}}, {{链接}}, {{随机字符串}}, {{日期}}, {{UUID}}。"
                        },
                        {
                            "role": "user",
                            "content": f"請生成 {count} 個郵件模板，主題：{prompt}"
                        }
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                # 嘗試解析 JSON
                try:
                    # 移除可能的 markdown 代碼塊標記
                    content = content.strip()
                    if content.startswith('```'):
                        content = content.split('\n', 1)[1]
                    if content.endswith('```'):
                        content = content.rsplit('\n', 1)[0]
                    
                    templates = json.loads(content)
                    
                    # 保存模板
                    template_manager = TemplateManager("templates")
                    saved_count = 0
                    
                    if isinstance(templates, list):
                        for template in templates:
                            if template_manager.save_template(template):
                                saved_count += 1
                    elif isinstance(templates, dict):
                        if template_manager.save_template(templates):
                            saved_count += 1
                    
                    self.progress_label.setText(f"成功生成並保存 {saved_count} 個模板")
                    QMessageBox.information(self, "成功", f"已生成並保存 {saved_count} 個模板")
                except json.JSONDecodeError:
                    self.progress_label.setText("解析失敗")
                    QMessageBox.warning(self, "警告", "無法解析生成的模板")
            else:
                self.progress_label.setText("生成失敗")
                QMessageBox.warning(self, "警告", f"生成失敗: {response.text}")
        
        except Exception as e:
            self.progress_label.setText("發生錯誤")
            QMessageBox.critical(self, "錯誤", str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("郵件發送系統")
        self.setMinimumSize(1000, 700)
        
        self.sender_manager = SenderManager()
        self.sender_manager.on_progress = self.update_progress
        self.sender_manager.on_log = self.append_log
        self.sender_manager.on_complete = self.on_sending_complete
        
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # 創建標籤頁
        tabs = QTabWidget()
        
        # API 配置標籤
        api_tab = self.create_api_tab()
        tabs.addTab(api_tab, "API 配置")
        
        # 模板管理標籤
        template_tab = self.create_template_tab()
        tabs.addTab(template_tab, "模板管理")
        
        # AI 生成標籤
        ai_tab = self.create_ai_tab()
        tabs.addTab(ai_tab, "AI 生成")
        
        # 發送郵件標籤
        send_tab = self.create_send_tab()
        tabs.addTab(send_tab, "發送郵件")
        
        main_layout.addWidget(tabs)
        central_widget.setLayout(main_layout)

    def create_api_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 按鈕區域
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加 API")
        add_btn.clicked.connect(self.add_api)
        edit_btn = QPushButton("編輯 API")
        edit_btn.clicked.connect(self.edit_api)
        delete_btn = QPushButton("刪除 API")
        delete_btn.clicked.connect(self.delete_api)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_apis)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        
        # API 表格
        self.api_table = QTableWidget()
        self.api_table.setColumnCount(2)
        self.api_table.setHorizontalHeaderLabels(["名稱", "發件郵箱"])
        self.api_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.api_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.api_table)
        widget.setLayout(layout)
        
        self.refresh_apis()
        return widget

    def create_template_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 按鈕區域
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加模板")
        add_btn.clicked.connect(self.add_template)
        edit_btn = QPushButton("編輯模板")
        edit_btn.clicked.connect(self.edit_template)
        delete_btn = QPushButton("刪除模板")
        delete_btn.clicked.connect(self.delete_template)
        preview_btn = QPushButton("預覽")
        preview_btn.clicked.connect(self.preview_template)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_templates)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(preview_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        
        # 模板表格
        self.template_table = QTableWidget()
        self.template_table.setColumnCount(4)
        self.template_table.setHorizontalHeaderLabels(["名稱", "主題", "格式", "文件名"])
        self.template_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.template_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.template_table)
        widget.setLayout(layout)
        
        self.refresh_templates()
        return widget

    def create_ai_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        info_label = QLabel("使用 OpenRouter API 自動生成郵件模板")
        info_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        generate_btn = QPushButton("打開 AI 生成對話框")
        generate_btn.clicked.connect(self.open_ai_dialog)
        generate_btn.setMinimumHeight(40)
        
        layout.addWidget(info_label)
        layout.addWidget(generate_btn)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_send_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 收件人區域
        recipients_group = QGroupBox("收件人")
        recipients_layout = QVBoxLayout()
        self.recipients_input = QTextEdit()
        self.recipients_input.setPlaceholderText("每行一個郵箱地址")
        self.recipients_input.setMaximumHeight(100)
        recipients_layout.addWidget(self.recipients_input)
        recipients_group.setLayout(recipients_layout)
        
        # URL 輪換池
        url_group = QGroupBox("URL 輪換池")
        url_layout = QVBoxLayout()
        self.url_pool_input = QTextEdit()
        self.url_pool_input.setPlaceholderText("每行一個 URL")
        self.url_pool_input.setMaximumHeight(80)
        self.url_pool_enabled = QCheckBox("啟用 URL 輪換")
        url_layout.addWidget(self.url_pool_input)
        url_layout.addWidget(self.url_pool_enabled)
        url_group.setLayout(url_layout)
        
        # 郵件內容
        content_group = QGroupBox("郵件內容")
        content_layout = QFormLayout()
        
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("支持變數: {{发件人}}, {{收件人}}, {{链接}}, {{随机字符串}}, {{日期}}, {{UUID}}")
        
        self.body_input = QTextEdit()
        self.body_input.setMinimumHeight(150)
        self.body_input.setPlaceholderText("郵件正文，支持變數替換")
        
        self.is_html = QCheckBox("HTML 格式")
        
        content_layout.addRow("主題:", self.subject_input)
        content_layout.addRow(self.is_html)
        content_layout.addRow("正文:", self.body_input)
        content_group.setLayout(content_layout)
        
        # 發送設置
        settings_group = QGroupBox("發送設置")
        settings_layout = QFormLayout()
        
        self.batch_size_input = QSpinBox()
        self.batch_size_input.setRange(1, 100)
        self.batch_size_input.setValue(1)
        
        self.max_concurrent_input = QSpinBox()
        self.max_concurrent_input.setRange(1, 10)
        self.max_concurrent_input.setValue(1)
        
        self.batch_interval_input = QSpinBox()
        self.batch_interval_input.setRange(0, 60)
        self.batch_interval_input.setValue(1)
        self.batch_interval_input.setSuffix(" 秒")
        
        self.same_domain_delay_input = QSpinBox()
        self.same_domain_delay_input.setRange(0, 60)
        self.same_domain_delay_input.setValue(1)
        self.same_domain_delay_input.setSuffix(" 秒")
        
        settings_layout.addRow("批次大小:", self.batch_size_input)
        settings_layout.addRow("最大並發:", self.max_concurrent_input)
        settings_layout.addRow("批次間隔:", self.batch_interval_input)
        settings_layout.addRow("同域延遲:", self.same_domain_delay_input)
        settings_group.setLayout(settings_layout)
        
        # 控制按鈕
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("開始")
        self.start_btn.clicked.connect(self.start_sending)
        self.pause_btn = QPushButton("暫停")
        self.pause_btn.clicked.connect(self.pause_sending)
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_sending)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.stop_btn)
        
        # 進度顯示
        progress_group = QGroupBox("進度")
        progress_layout = QVBoxLayout()
        
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("總數: 0")
        self.sent_label = QLabel("已發送: 0")
        self.success_label = QLabel("成功: 0")
        self.failed_label = QLabel("失敗: 0")
        self.rate_label = QLabel("速度: 0 封/秒")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.sent_label)
        stats_layout.addWidget(self.success_label)
        stats_layout.addWidget(self.failed_label)
        stats_layout.addWidget(self.rate_label)
        
        self.progress_bar = QProgressBar()
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)
        
        progress_layout.addLayout(stats_layout)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(QLabel("日誌:"))
        progress_layout.addWidget(self.log_output)
        progress_group.setLayout(progress_layout)
        
        # 主要佈局
        main_content = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.addWidget(recipients_group)
        left_layout.addWidget(url_group)
        left_layout.addWidget(content_group)
        
        right_layout = QVBoxLayout()
        right_layout.addWidget(settings_group)
        right_layout.addLayout(control_layout)
        right_layout.addWidget(progress_group)
        
        main_content.addLayout(left_layout, 2)
        main_content.addLayout(right_layout, 1)
        
        layout.addLayout(main_content)
        widget.setLayout(layout)
        return widget

    def refresh_apis(self):
        """刷新 API 列表"""
        try:
            apis_file = os.path.join(APP_DIR, "data", "apis.json")
            with open(apis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.api_table.setRowCount(len(data))
            for row, (key, value) in enumerate(data.items()):
                self.api_table.setItem(row, 0, QTableWidgetItem(value.get('name', key)))
                self.api_table.setItem(row, 1, QTableWidgetItem(value.get('from_email', '')))
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加載 API 失敗: {e}")

    def add_api(self):
        dialog = ApiConfigDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                apis_file = os.path.join(APP_DIR, "data", "apis.json")
                with open(apis_file, 'r', encoding='utf-8') as f:
                    apis = json.load(f)
                
                apis[data['name']] = data
                
                with open("os.path.join(APP_DIR, data, apis.json)", 'w', encoding='utf-8') as f:
                    json.dump(apis, f, ensure_ascii=False, indent=2)
                
                self.refresh_apis()
                QMessageBox.information(self, "成功", "API 添加成功")
            except Exception as e:
                QMessageBox.critical(self, "錯誤", str(e))

    def edit_api(self):
        row = self.api_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "警告", "請選擇要編輯的 API")
            return
        
        name = self.api_table.item(row, 0).text()
        
        try:
            with open("os.path.join(APP_DIR, data, apis.json)", 'r', encoding='utf-8') as f:
                apis = json.load(f)
            
            api_data = apis.get(name, {})
            dialog = ApiConfigDialog(self, api_data)
            
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                old_name = api_data.get('name', name)
                
                if old_name in apis:
                    del apis[old_name]
                
                apis[data['name']] = data
                
                with open("os.path.join(APP_DIR, data, apis.json)", 'w', encoding='utf-8') as f:
                    json.dump(apis, f, ensure_ascii=False, indent=2)
                
                self.refresh_apis()
                QMessageBox.information(self, "成功", "API 更新成功")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", str(e))

    def delete_api(self):
        row = self.api_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "警告", "請選擇要刪除的 API")
            return
        
        name = self.api_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, "確認刪除", f"確定要刪除 API '{name}' 嗎?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with open("os.path.join(APP_DIR, data, apis.json)", 'r', encoding='utf-8') as f:
                    apis = json.load(f)
                
                if name in apis:
                    del apis[name]
                    
                    with open("os.path.join(APP_DIR, data, apis.json)", 'w', encoding='utf-8') as f:
                        json.dump(apis, f, ensure_ascii=False, indent=2)
                    
                    self.refresh_apis()
                    QMessageBox.information(self, "成功", "API 刪除成功")
            except Exception as e:
                QMessageBox.critical(self, "錯誤", str(e))

    def refresh_templates(self):
        """刷新模板列表"""
        try:
            template_manager = TemplateManager("templates")
            templates = template_manager.get_templates()
            
            self.template_table.setRowCount(len(templates))
            for row, template in enumerate(templates):
                self.template_table.setItem(row, 0, QTableWidgetItem(template.get('name', '')))
                self.template_table.setItem(row, 1, QTableWidgetItem(template.get('subject', '')))
                self.template_table.setItem(row, 2, QTableWidgetItem('HTML' if template.get('is_html') else 'Text'))
                self.template_table.setItem(row, 3, QTableWidgetItem(template.get('filename', '')))
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加載模板失敗: {e}")

    def add_template(self):
        dialog = TemplateDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                template_manager = TemplateManager("templates")
                if template_manager.save_template(data):
                    self.refresh_templates()
                    QMessageBox.information(self, "成功", "模板添加成功")
                else:
                    QMessageBox.warning(self, "警告", "模板保存失敗")
            except Exception as e:
                QMessageBox.critical(self, "錯誤", str(e))

    def edit_template(self):
        row = self.template_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "警告", "請選擇要編輯的模板")
            return
        
        filename = self.template_table.item(row, 3).text()
        
        try:
            template_manager = TemplateManager("templates")
            templates = template_manager.get_templates()
            
            template_data = next((t for t in templates if t.get('filename') == filename), None)
            if template_data:
                dialog = TemplateDialog(self, template_data)
                
                if dialog.exec() == QDialog.Accepted:
                    data = dialog.get_data()
                    if template_manager.save_template(data, filename):
                        self.refresh_templates()
                        QMessageBox.information(self, "成功", "模板更新成功")
                    else:
                        QMessageBox.warning(self, "警告", "模板保存失敗")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", str(e))

    def delete_template(self):
        row = self.template_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "警告", "請選擇要刪除的模板")
            return
        
        filename = self.template_table.item(row, 3).text()
        
        reply = QMessageBox.question(
            self, "確認刪除", f"確定要刪除模板嗎?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                template_manager = TemplateManager("templates")
                if template_manager.delete_template(filename):
                    self.refresh_templates()
                    QMessageBox.information(self, "成功", "模板刪除成功")
            except Exception as e:
                QMessageBox.critical(self, "錯誤", str(e))

    def preview_template(self):
        row = self.template_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "警告", "請選擇要預覽的模板")
            return
        
        filename = self.template_table.item(row, 3).text()
        
        try:
            template_manager = TemplateManager("templates")
            templates = template_manager.get_templates()
            
            template_data = next((t for t in templates if t.get('filename') == filename), None)
            if template_data:
                context = {
                    "sender": "示例發件人",
                    "recipient": "example@test.com",
                    "link": "https://example.com"
                }
                template_manager.preview_template(template_data, context)
        except Exception as e:
            QMessageBox.critical(self, "錯誤", str(e))

    def open_ai_dialog(self):
        dialog = AiTemplateDialog(self)
        dialog.exec()

    def start_sending(self):
        """開始發送"""
        recipients = self.recipients_input.toPlainText().strip()
        if not recipients:
            QMessageBox.warning(self, "警告", "請輸入收件人")
            return
        
        params = {
            'recipients': recipients,
            'url_pool': self.url_pool_input.toPlainText(),
            'url_pool_enabled': self.url_pool_enabled.isChecked(),
            'subject': self.subject_input.text(),
            'body': self.body_input.toPlainText(),
            'is_html': self.is_html.isChecked(),
            'batch_size': self.batch_size_input.value(),
            'max_concurrent': self.max_concurrent_input.value(),
            'batch_interval': self.batch_interval_input.value(),
            'same_domain_delay': self.same_domain_delay_input.value()
        }
        
        if self.sender_manager.start_sending(params):
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)

    def pause_sending(self):
        """暫停發送"""
        self.sender_manager.pause_sending()
        self.pause_btn.setText("恢復")
        self.pause_btn.clicked.disconnect()
        self.pause_btn.clicked.connect(self.resume_sending)

    def resume_sending(self):
        """恢復發送"""
        self.sender_manager.resume_sending()
        self.pause_btn.setText("暫停")
        self.pause_btn.clicked.disconnect()
        self.pause_btn.clicked.connect(self.pause_sending)

    def stop_sending(self):
        """停止發送"""
        self.sender_manager.stop_sending()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

    def update_progress(self, progress):
        """更新進度"""
        self.total_label.setText(f"總數: {progress['total']}")
        self.sent_label.setText(f"已發送: {progress['sent']}")
        self.success_label.setText(f"成功: {progress['success']}")
        self.failed_label.setText(f"失敗: {progress['failed']}")
        self.rate_label.setText(f"速度: {progress['rate']} 封/秒")
        
        if progress['total'] > 0:
            value = int((progress['sent'] / progress['total']) * 100)
            self.progress_bar.setValue(value)

    def append_log(self, message):
        """追加日誌"""
        self.log_output.append(message)
        # 自動滾動到底部
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_sending_complete(self):
        """發送完成"""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)


if __name__ == "__main__":
    # 自動創建必要的目錄結構
    for directory in ['config', 'data', 'logs', 'templates', 'data/send_logs']:
        dir_path = os.path.join(APP_DIR, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    # 確保 apis.json 存在
    apis_file = os.path.join(APP_DIR, 'data', 'apis.json')
    if not os.path.exists(apis_file):
        # 創建符合 schema 的空殼文件
        with open(apis_file, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())