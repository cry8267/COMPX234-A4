import socket
import sys
import base64
import os

class UDPClient:
    def __init__(self, host, port, file_list):
        self.host = host
        self.port = port
        self.file_list = file_list
        self.socket = None
        self.max_retries = 5
        self.initial_timeout = 1.0

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(1.0)
            with open(self.file_list, 'r') as f:
                files_to_download = [line.strip() for line in f if line.strip()]
        
            if not files_to_download:
                print("Error: The file list is empty.")
                return

            for filename in files_to_download:
                try:
                    self.download_file(filename)
                except Exception as e:
                    print(f"Download {filename} Failure: {e}")
                    continue
        except FileNotFoundError:
            print(f"Error: File list {self.file_list} Doesn't exist")
        except Exception as e:
            print(f"Unable to read the file list.: {e}")
        finally:
            if self.socket:
                self.socket.close()

    def download_file(self, filename):
        print(f"\nStart downloading: {filename}")
        
        try:
            # Send DOWNLOAD request
            response = self.reliable_send_receive(
                f"DOWNLOAD {filename}",
                (self.host, self.port)
            )
        
            if response.startswith("ERR"):
                print(f"Download failed: {response}")
                return
                
            # Analyze response
            parts = response.split()
            if len(parts) != 6 or parts[0] != "OK":
                print("Invalid server response")
                return
                
            file_size = int(parts[3])
            data_port = int(parts[5])
            
            print(f"File size: {file_size} Byte")
            print("Download progress: [", end='', flush=True)
            
            # Start receiving files
            self.receive_file_data(filename, file_size, data_port)
            
            print("] Completed")
            
        except Exception as e:
            print(f"\nDownload {filename} : {e}Failure")
            raise

    def receive_file_data(self, filename, file_size, data_port):
        downloaded = 0
        block_size = 1000 
        
        # Ensure the download directory exists
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
                    raise Exception(f"Invalid response: {response}")
                    
                # Extract and decode data
                data_start = response.find("DATA") + 5
                base64_data = response[data_start:]
                binary_data = base64.b64decode(base64_data)
                
                file.seek(start)
                file.write(binary_data)
                downloaded += len(binary_data)
                
                print("#", end='', flush=True)
            
            self.reliable_send_receive(
                f"FILE {filename} CLOSE",
                (self.host, data_port)
            )

    def reliable_send_receive(self, message, address):
        current_timeout = 1.0  
        attempt = 0
        while attempt < self.max_retries:
            try:
                
                self.socket.sendto(message.encode(), address)
                self.socket.settimeout(current_timeout)
                response, _ = self.socket.recvfrom(65535)
                print(f"Received response: {response.decode()}")
                return response.decode()
                
            except socket.timeout:
                attempt += 1
                if attempt >= self.max_retries:
                    raise Exception(f" The server did not respond, retrying.{self.max_retries} 次")
                print(f"Overtime(Try{attempt}/{self.max_retries}), 重试...")
                current_timeout *= 2
                
        raise Exception("Reached the maximum number of retries, the server did not respond.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python UDPclient.py <host> <Port> <File list>")
        sys.exit(1)
        
    try:
        host = sys.argv[1]
        port = int(sys.argv[2])
        file_list = sys.argv[3]
        
        client = UDPClient(host, port, file_list)
        client.start()
        
    except ValueError:
        print("Error: The port number must be an integer.")
    except Exception as e:
        print(f"Client error: {e}")