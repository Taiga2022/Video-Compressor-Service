import socket
import sys
import os

def upload_file(server_address, file_path):
    if not os.path.isfile(file_path):
        print("File does not exist")
        return

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(server_address)
    except socket.error as e:
        print(f"Connection error: {e}")
        sys.exit(1)

    try:
        file_size = os.path.getsize(file_path)
        print(f'Sending file size: {file_size} bytes')
        sock.sendall(str(file_size).ljust(32).encode('utf-8'))

        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(1400)
                if not chunk:
                    break
                sock.sendall(chunk)

        response = sock.recv(16).decode('utf-8').strip()
        print(f"Server response: {response}")
    finally:
        print("Closing socket")
        sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    server_address = '/tmp/server.sock'
    upload_file(server_address, file_path)
