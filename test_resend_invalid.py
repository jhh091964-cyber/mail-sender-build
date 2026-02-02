"""
測試使用無效 Resend API Key 發送郵件（應該失敗）
"""
import sys
import json
from resend_provider import ResendProvider

def test_invalid_api_key():
    print("=" * 50)
    print("Resend API 測試 - 無效 API Key")
    print("=" * 50)
    
    # 使用無效的 API Key
    invalid_api_key = "re_invalid_test_key_12345"
    
    print(f"\n使用 API Key: {invalid_api_key}")
    print(f"發送郵件至: test@example.com")
    
    provider = ResendProvider(api_key=invalid_api_key)
    
    payload = {
        "from": "test@example.com",
        "to": ["recipient@example.com"],
        "subject": "測試郵件 - 無效 API Key",
        "text": "這是一封測試郵件"
    }
    
    print(f"\n正在發送請求...")
    status_code, response, response_text = provider.send_one(payload)
    
    print(f"\n結果:")
    print(f"  HTTP Status Code: {status_code}")
    print(f"  Response JSON: {json.dumps(response, indent=2) if response else 'None'}")
    print(f"  Response Text: {response_text}")
    
    if status_code in [401, 403]:
        print(f"\n✓ 測試通過：無效 API Key 正確返回 401/403")
    else:
        print(f"\n✗ 測試失敗：預期 401/403，實際返回 {status_code}")
    
    print("\n" + "=" * 50)
    print("測試完成")
    print("=" * 50)

if __name__ == "__main__":
    test_invalid_api_key()