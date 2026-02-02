"""
SSH 隧道測試腳本
測試 SOCKS5 代理是否正常工作
"""
import sys
import requests
from ssh_tunnel import SSHTunnel

def test_ssh_tunnel():
    print("=" * 50)
    print("SSH 隧道測試")
    print("=" * 50)
    
    # 測試配置（需要真實的 SSH 伺服器）
    config = {
        'ssh_host': 'example.com',
        'ssh_port': 22,
        'ssh_username': 'testuser',
        'ssh_password': 'testpass',
        'ssh_key_file': '',
        'local_port': 10800
    }
    
    print(f"\nSSH 配置:")
    print(f"  主機: {config['ssh_host']}")
    print(f"  端口: {config['ssh_port']}")
    print(f"  用戶名: {config['ssh_username']}")
    print(f"  本地端口: {config['local_port']}")
    
    tunnel = SSHTunnel(
        ssh_host=config['ssh_host'],
        ssh_port=config['ssh_port'],
        ssh_username=config['ssh_username'],
        ssh_password=config['ssh_password'],
        ssh_key_file=config['ssh_key_file'],
        local_port=config['local_port']
    )
    
    print(f"\n正在連接 SSH...")
    connected = tunnel.connect()
    
    if connected:
        print(f"✓ SSH 連接成功")
        print(f"✓ SOCKS5 代理已啟動於 127.0.0.1:{config['local_port']}")
        
        # 測試通過 SOCKS5 代理請求
        proxies = {
            'http': tunnel.get_proxy_url(),
            'https': tunnel.get_proxy_url()
        }
        
        print(f"\n代理 URL: {tunnel.get_proxy_url()}")
        print(f"\n正在通過代理測試 HTTPS 請求...")
        
        try:
            response = requests.get(
                'https://api.ipify.org?format=json',
                proxies=proxies,
                timeout=30
            )
            print(f"✓ HTTPS 請求成功")
            print(f"  狀態碼: {response.status_code}")
            print(f"  響應: {response.text}")
        except Exception as e:
            print(f"✗ HTTPS 請求失敗: {e}")
        
        tunnel.disconnect()
        print(f"\nSSH 連接已關閉")
    else:
        print(f"✗ SSH 連接失敗")
        print(f"  請檢查 SSH 配置是否正確")
    
    print("\n" + "=" * 50)
    print("測試完成")
    print("=" * 50)

if __name__ == "__main__":
    test_ssh_tunnel()