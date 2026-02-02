import re
import uuid
from datetime import datetime
import random
import string

class VariableParser:
    @staticmethod
    def parse(text: str, context: dict) -> str:
        if not text:
            return text
        
        # 變數映射
        variables = {
            "发件人": context.get("sender", ""),
            "收件人": context.get("recipient", ""),
            "链接": context.get("link", ""),
            "随机字符串": VariableParser._generate_random_string(),
            "日期": datetime.now().strftime("%Y-%m-%d"),
            "UUID": str(uuid.uuid4())
        }
        
        # 替換所有變數
        for var_name, var_value in variables.items():
            pattern = r"\{\{" + re.escape(var_name) + r"\}\}"
            text = re.sub(pattern, str(var_value), text)
        
        return text
    
    @staticmethod
    def _generate_random_string(length: int = 8) -> str:
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))