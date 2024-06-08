import socket
import os

def start_server(server_address):
    if os.path.exists(server_address):
        os.unlink(server_address)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen(1)
    print('Server started, waiting for connections...')

    while True:
        connection, client_address = sock.accept()
        try:
            print('Connection from', client_address)
            # 最初の32バイトはファイルサイズ
            file_size_data = connection.recv(32)
            if not file_size_data:
                break

            file_size = int(file_size_data.decode('utf-8').strip())
            print(f'Received file size: {file_size} bytes')

            file_data = b''
            while len(file_data) < file_size:
                packet = connection.recv(1400)
                if not packet:
                    break
                file_data += packet

            # 保存するファイル名
            with open('output/received_file.mp4', 'wb') as f:
                f.write(file_data)

            print(f'File received successfully. Size: {len(file_data)} bytes')
            response = "UPLOAD SUCCESS"
            connection.sendall(response.ljust(16).encode('utf-8'))
        except Exception as e:
            print(f"Error: {e}")
            response = "UPLOAD FAILED"
            connection.sendall(response.ljust(16).encode('utf-8'))
        finally:
            connection.close()

if __name__ == "__main__":
    server_address = '/tmp/server.sock'
    start_server(server_address)
