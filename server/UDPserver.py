import socket
import os
import sys
import random

if len(sys.argv) != 2:
    print("Usage: python3 UDPserver.py <port>")
    sys.exit(1)

server_port = int(sys.argv[1])
buffer_size = 4096

# 创建 socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', server_port))
print(f"[SERVER] Listening on port {server_port}...")

while True:
    print("[SERVER] Waiting for message...")
    message, client_address = server_socket.recvfrom(buffer_size)
    message_str = message.decode().strip()
    print(f"[RECEIVED] From {client_address}: {message_str}")

    if message_str.startswith("DOWNLOAD"):
        parts = message_str.split()
        if len(parts) != 2:
            print("[ERROR] Malformed DOWNLOAD message")
            continue

        filename = parts[1]
        file_path = os.path.join("server", filename)
        print(f"[SERVER] Checking file: {file_path}")

        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            port_number = random.randint(50000, 51000)
            response = f"OK {filename} SIZE {file_size} PORT {port_number}"
        else:
            response = f"ERR {filename} NOT_FOUND"

        server_socket.sendto(response.encode(), client_address)
        print(f"[SENT] {response}")
