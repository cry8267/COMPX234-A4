import socket
import sys
import base64
import os

class UDPClient:
    def __init__(self, host, port, file_list):
        self.host = host
        self.port = port
        self.file_list = file_list
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(1.0)  # 默认超时1秒
        self.max_retries = 5

    def start(self):
        try:
            with open(self.file_list, 'r') as f:
                files_to_download = [line.strip() for line in f if line.strip()]
                
            if not files_to_download:
                print("错误: 文件列表为空")
                return
                
            for filename in files_to_download:
                self.download_file(filename)
                
        except FileNotFoundError:
            print(f"错误: 文件列表 {self.file_list} 不存在")
        except Exception as e:
            print(f"客户端错误: {e}")
        finally:
            self.socket.close()

    def download_file(self, filename):
        print(f"\n开始下载: {filename}")
        
        try:
            # 发送DOWNLOAD请求
            response = self.reliable_send_receive(
                f"DOWNLOAD {filename}",
                (self.host, self.port)
            )
            
            if response.startswith("ERR"):
                print(f"下载失败: {response}")
                return
                
            # 解析响应
            parts = response.split()
            if len(parts) != 6 or parts[0] != "OK":
                print("无效的服务器响应")
                return
                
            file_size = int(parts[3])
            data_port = int(parts[5])
            
            print(f"文件大小: {file_size} 字节")
            print("下载进度: [", end='', flush=True)
            
            # 开始接收文件
            self.receive_file_data(filename, file_size, data_port)
            
            print("] 完成")
            
        except Exception as e:
            print(f"\n下载 {filename} 失败: {e}")

    def receive_file_data(self, filename, file_size, data_port):
        downloaded = 0
        block_size = 1000  # 每个数据块1000字节
        
        # 确保下载目录存在
        os.makedirs("downloads", exist_ok=True)
        filepath = os.path.join("downloads", filename)
        
        with open(filepath, 'wb') as file:
            while downloaded < file_size:
                start = downloaded
                end = min(downloaded + block_size - 1, file_size - 1)
                
                response = self.reliable_send_receive(
                    f"FILE {filename} GET START {start} END {end}",
                    (self.host, data_port)
                )
                
                if not response.startswith(f"FILE {filename} OK"):
                    raise Exception(f"无效的响应: {response}")
                    
                # 提取并解码数据
                data_start = response.find("DATA") + 5
                base64_data = response[data_start:]
                binary_data = base64.b64decode(base64_data)
                
                file.seek(start)
                file.write(binary_data)
                downloaded += len(binary_data)
                
                # 显示进度
                print("#", end='', flush=True)
            
            # 发送关闭请求
            self.reliable_send_receive(
                f"FILE {filename} CLOSE",
                (self.host, data_port)
            )

    def reliable_send_receive(self, message, address):
        current_timeout = 1.0  # 初始超时1秒
        attempt = 0
        
        while attempt < self.max_retries:
            try:
                self.socket.sendto(message.encode(), address)
                self.socket.settimeout(current_timeout)
                
                response, _ = self.socket.recvfrom(65535)
                return response.decode()
                
            except socket.timeout:
                attempt += 1
                if attempt < self.max_retries:
                    print(f"超时 (尝试 {attempt}/{self.max_retries}), 重试...")
                    current_timeout *= 2  # 指数退避
                continue
                
        raise Exception("达到最大重试次数，服务器无响应")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("用法: python UDPclient.py <主机> <端口> <文件列表>")
        sys.exit(1)
        
    try:
        host = sys.argv[1]
        port = int(sys.argv[2])
        file_list = sys.argv[3]
        
        client = UDPClient(host, port, file_list)
        client.start()
        
    except ValueError:
        print("错误: 端口号必须是整数")
    except Exception as e:
        print(f"客户端错误: {e}")