# UDPclient.py
import socket
import sys

def main():
    if len(sys.argv) != 4:
        print("用法: python UDPclient.py <主机> <端口> <文件列表>")
        return
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    file_list = sys.argv[3]
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(b"Hello Server", (host, port))
    print("消息已发送")

if __name__ == "__main__":
    main()