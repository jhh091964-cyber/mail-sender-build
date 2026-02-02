import json
import os
import sys
import webbrowser
from typing import List, Dict, Optional
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

class TemplateManager:
    def __init__(self, templates_dir: str = "templates"):
        # 如果傳入的是相對路徑，則以 APP_DIR 為基礎
        if not os.path.isabs(templates_dir):
            self.templates_dir = os.path.join(APP_DIR, templates_dir)
        else:
            self.templates_dir = templates_dir
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)

    def get_templates(self) -> List[Dict]:
        """獲取所有模板"""
        templates = []
        if not os.path.exists(self.templates_dir):
            return templates
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.templates_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                        template['filename'] = filename
                        templates.append(template)
                except Exception as e:
                    print(f"讀取模板失敗 {filename}: {e}")
        
        return templates

    def save_template(self, template: Dict, filename: str = None) -> bool:
        """保存模板"""
        try:
            self._ensure_dir()
            if not filename:
                # 自動生成文件名
                count = len(self.get_templates()) + 1
                filename = f"template_{count}.json"
            
            filepath = os.path.join(self.templates_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存模板失敗: {e}")
            return False

    def delete_template(self, filename: str) -> bool:
        """刪除模板"""
        try:
            filepath = os.path.join(self.templates_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            print(f"刪除模板失敗: {e}")
        return False

    def preview_template(self, template: Dict, context: Dict):
        """預覽模板（在瀏覽器中打開渲染後的 HTML）"""
        try:
            html_content = template.get('content', '')
            if template.get('is_html', False):
                # 替換變數
                rendered = VariableParser.parse(html_content, context)
                
                # 保存到臨時文件並打開
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(rendered)
                    temp_file = f.name
                
                webbrowser.open('file://' + os.path.abspath(temp_file))
            else:
                # 純文本預覽 - 轉換為 HTML 以便在瀏覽器中查看
                rendered = VariableParser.parse(html_content, context)
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>預覽</title></head>'
                           f'<body style="font-family: monospace; white-space: pre-wrap;">{rendered}</body></html>')
                    temp_file = f.name
                
                webbrowser.open('file://' + os.path.abspath(temp_file))
        except Exception as e:
            print(f"預覽模板失敗: {e}")

    def get_next_template(self, templates: List[Dict], index: int) -> Optional[Dict]:
        """輪詢獲取下一個模板"""
        if not templates:
            return None
        return templates[index % len(templates)]