import paramiko
import socket
import threading
import time
import struct
from typing import Optional

class SSHTunnel:
    def __init__(self, ssh_host: str, ssh_port: int, ssh_username: str, 
                 ssh_password: str, ssh_key_file: str, local_port: int):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.ssh_key_file = ssh_key_file
        self.local_port = local_port
        self.client = None
        self.server_socket = None
        self.thread = None
        self.running = False

    def connect(self) -> bool:
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.ssh_key_file:
                private_key = paramiko.RSAKey.from_private_key_file(self.ssh_key_file)
                self.client.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_username,
                    pkey=private_key,
                    timeout=30
                )
            else:
                self.client.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_username,
                    password=self.ssh_password,
                    timeout=30
                )
            
            self.running = True
            self.thread = threading.Thread(target=self._run_socks5_server)
            self.thread.daemon = True
            self.thread.start()
            return True
        except Exception as e:
            print(f"SSH 連接失敗: {e}")
            return False

    def _run_socks5_server(self):
        """運行本地 SOCKS5 代理服務器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('127.0.0.1', self.local_port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1)
            
            print(f"SOCKS5 代理已啟動於 127.0.0.1:{self.local_port}")
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    threading.Thread(
                        target=self._handle_socks5_client,
                        args=(client_socket,),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"接受連接錯誤: {e}")
                    break
        except Exception as e:
            print(f"SOCKS5 服務器錯誤: {e}")
        finally:
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass

    def _handle_socks5_client(self, client_socket):
        """處理 SOCKS5 客戶端連接"""
        try:
            # SOCKS5 握手 - 第一步：接收客戶端 greeting
            greeting = client_socket.recv(262)
            if len(greeting) < 2:
                client_socket.close()
                return
            
            ver, nmethods = greeting[0], greeting[1]
            if ver != 0x05:
                client_socket.close()
                return
            
            # 發送方法選擇響應（無需認證）
            client_socket.send(b'\x05\x00')
            
            # 接收 CONNECT 請求
            request = client_socket.recv(4)
            if len(request) < 4:
                client_socket.close()
                return
            
            version, cmd, rsv = request[:3]
            
            if version != 0x05 or cmd != 0x01:  # 只支持 CONNECT
                client_socket.send(b'\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00')  # 不支持的命令
                client_socket.close()
                return
            
            # 讀取目標地址
            atyp = request[3]
            if atyp == 0x01:  # IPv4
                addr_bytes = client_socket.recv(4)
                dest_addr = socket.inet_ntoa(addr_bytes)
            elif atyp == 0x03:  # 域名
                addr_len = struct.unpack('B', client_socket.recv(1))[0]
                dest_addr = client_socket.recv(addr_len).decode('utf-8')
            else:  # IPv6 或其他不支持的類型
                client_socket.send(b'\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00')
                client_socket.close()
                return
            
            # 讀取端口
            port_bytes = client_socket.recv(2)
            dest_port = struct.unpack('!H', port_bytes)[0]
            
            # 通過 SSH 隧道轉發
            try:
                ssh_channel = self.client.get_transport().open_channel(
                    'direct-tcpip',
                    (dest_addr, dest_port),
                    ('127.0.0.1', self.local_port)
                )
                
                # 發送成功響應
                client_socket.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
                
                # 雙向轉發數據
                self._forward_data(client_socket, ssh_channel)
                
            except Exception as e:
                client_socket.send(b'\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00')  # 連接失敗
                print(f"SSH 隧道轉發失敗: {e}")
                
        except Exception as e:
            print(f"處理 SOCKS5 客戶端錯誤: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def _forward_data(self, client_socket, ssh_channel):
        """雙向轉發數據"""
        try:
            import select
            
            sockets = [client_socket, ssh_channel]
            
            while self.running:
                r, _, _ = select.select(sockets, [], [], 1)
                
                if not r:
                    continue
                
                for sock in r:
                    if sock == client_socket:
                        data = client_socket.recv(4096)
                        if not data:
                            return
                        ssh_channel.send(data)
                    elif sock == ssh_channel:
                        data = ssh_channel.recv(4096)
                        if not data:
                            return
                        client_socket.send(data)
                        
        except Exception as e:
            print(f"數據轉發錯誤: {e}")

    def disconnect(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        if self.client:
            try:
                self.client.close()
            except:
                pass
        self.client = None
        self.server_socket = None

    def get_proxy_url(self) -> str:
        return f"socks5://127.0.0.1:{self.local_port}"