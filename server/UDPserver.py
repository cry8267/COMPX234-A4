import socket
import sys
import threading
import random
import os
import base64

class UDPServer:
    def __init__(self, port):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(('', port))
        print(f"服务器已启动，监听端口 {port}")

    def start(self):
        try:
            while True:
                data, client_addr = self.server_socket.recvfrom(1024)
                threading.Thread(
                    target=self.handle_download_request,
                    args=(data, client_addr)
                ).start()
        except KeyboardInterrupt:
            print("\n服务器关闭中...")
            self.server_socket.close()

    def handle_download_request(self, data, client_addr):
        try:
            request = data.decode().strip()
            parts = request.split()
            
            if len(parts) != 2 or parts[0] != "DOWNLOAD":
                return  # 忽略无效请求
                
            filename = parts[1]
            if not os.path.exists(filename):
                self.server_socket.sendto(
                    f"ERR {filename} NOT_FOUND".encode(),
                    client_addr
                )
                return
                
            file_size = os.path.getsize(filename)
            data_port = random.randint(50000, 51000)
            
            # 发送OK响应
            self.server_socket.sendto(
                f"OK {filename} SIZE {file_size} PORT {data_port}".encode(),
                client_addr
            )
            
            # 启动文件传输线程
            threading.Thread(
                target=self.handle_file_transfer,
                args=(filename, client_addr, data_port)
            ).start()
            
        except Exception as e:
            print(f"处理请求时出错: {e}")

    def handle_file_transfer(self, filename, client_addr, data_port):
        transfer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        transfer_socket.bind(('', data_port))
        
        try:
            with open(filename, 'rb') as file:
                while True:
                    data, addr = transfer_socket.recvfrom(1024)
                    request = data.decode().strip()
                    parts = request.split()
                    
                    if len(parts) < 3:
                        continue
                        
                    if parts[0] == "FILE" and parts[2] == "CLOSE":
                        transfer_socket.sendto(
                            f"FILE {filename} CLOSE_OK".encode(),
                            client_addr
                        )
                        print(f"文件 {filename} 传输完成")
                        break
                        
                    elif parts[0] == "FILE" and parts[2] == "GET":
                        try:
                            start = int(parts[4])
                            end = int(parts[6])
                            file.seek(start)
                            data = file.read(end - start + 1)
                            
                            encoded_data = base64.b64encode(data).decode()
                            response = (
                                f"FILE {filename} OK START {start} END {end} "
                                f"DATA {encoded_data}"
                            )
                            transfer_socket.sendto(response.encode(), client_addr)
                            
                        except (ValueError, IndexError) as e:
                            print(f"无效的文件请求: {request}")
                            continue
                            
        except Exception as e:
            print(f"文件传输错误: {e}")
        finally:
            transfer_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python UDPserver.py <端口号>")
        sys.exit(1)
        
    try:
        port = int(sys.argv[1])
        server = UDPServer(port)
        server.start()
    except ValueError:
        print("错误: 端口号必须是整数")
    except Exception as e:
        print(f"服务器错误: {e}")
