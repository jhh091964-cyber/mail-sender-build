from typing import Optional
from ssh_tunnel import SSHTunnel

class ProxyHandler:
    def __init__(self):
        self.ssh_tunnel: Optional[SSHTunnel] = None

    def setup_proxy(self, api_config: dict) -> Optional[dict]:
        proxies = None
        
        # 優先使用 SSH 隧道
        if api_config.get("ssh_enabled", False):
            self.ssh_tunnel = SSHTunnel(
                ssh_host=api_config["ssh_host"],
                ssh_port=api_config["ssh_port"],
                ssh_username=api_config["ssh_username"],
                ssh_password=api_config["ssh_password"],
                ssh_key_file=api_config["ssh_key_file"],
                local_port=api_config["ssh_local_port"]
            )
            if self.ssh_tunnel.connect():
                proxies = {
                    "http": self.ssh_tunnel.get_proxy_url(),
                    "https": self.ssh_tunnel.get_proxy_url()
                }
            else:
                self.ssh_tunnel = None
                proxies = None
        # 否則使用直接代理
        elif api_config.get("proxy_enabled", False):
            proxy_url = api_config.get("proxy_full_url", "")
            if not proxy_url:
                proxy_type = api_config.get("proxy_type", "http")
                proxy_host = api_config["proxy_host"]
                proxy_port = api_config["proxy_port"]
                proxy_username = api_config.get("proxy_username", "")
                proxy_password = api_config.get("proxy_password", "")
                
                if proxy_username and proxy_password:
                    proxy_url = f"{proxy_type}://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
                else:
                    proxy_url = f"{proxy_type}://{proxy_host}:{proxy_port}"
            
            if proxy_url:
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url
                }
        
        return proxies

    def cleanup(self):
        if self.ssh_tunnel:
            self.ssh_tunnel.disconnect()
            self.ssh_tunnel = None