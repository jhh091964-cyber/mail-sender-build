"""
測試使用有效 Resend API Key 發送郵件（應該成功）
"""
import sys
import json
import os
from datetime import datetime
from resend_provider import ResendProvider

def test_valid_api_key():
    print("=" * 50)
    print("Resend API 測試 - 有效 API Key")
    print("=" * 50)
    
    # 從環境變量或用戶輸入獲取有效的 API Key
    api_key = os.environ.get('RESEND_API_KEY', 're_test_real_key_placeholder')
    
    if api_key == 're_test_real_key_placeholder':
        print("\n錯誤：請設置環境變量 RESEND_API_KEY")
        print("例如：export RESEND_API_KEY=re_xxxxxxxxxxxxxxxxx")
        print("或在腳本中直接替換 api_key 變量")
        return
    
    print(f"\n使用 API Key: {api_key[:10]}...")
    print(f"發送郵件至: test@example.com")
    
    provider = ResendProvider(api_key=api_key)
    
    payload = {
        "from": "test@example.com",
        "to": ["recipient@example.com"],
        "subject": "測試郵件 - 有效 API Key",
        "text": "這是一封測試郵件"
    }
    
    print(f"\n正在發送請求...")
    status_code, response, response_text = provider.send_one(payload)
    
    print(f"\n結果:")
    print(f"  HTTP Status Code: {status_code}")
    print(f"  Response JSON: {json.dumps(response, indent=2) if response else 'None'}")
    print(f"  Response Text: {response_text}")
    
    if status_code in [200, 202]:
        email_id = response.get('id') if response else None
        print(f"\n✓ 測試通過：郵件發送成功")
        print(f"  Email ID: {email_id}")
        
        # 保存日誌
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "api_key": api_key[:10] + "...",
            "email_id": email_id,
            "response": response
        }
        
        log_file = "logs/test_resend_valid.json"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False, indent=2)
        
        print(f"\n日誌已保存至: {log_file}")
        print(f"日誌內容:")
        print(json.dumps(log_entry, indent=2))
    else:
        print(f"\n✗ 測試失敗：預期 200/202，實際返回 {status_code}")
    
    print("\n" + "=" * 50)
    print("測試完成")
    print("=" * 50)

if __name__ == "__main__":
    test_valid_api_key()
