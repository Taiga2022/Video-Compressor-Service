import socket
import sys
import os
import json

# プロトコルヘッダの作成関数
def protocol_header(json_length, media_type_length, payload_length):
    return json_length.to_bytes(2, "big") + media_type_length.to_bytes(1, "big") + payload_length.to_bytes(5, "big")

# サーバに接続するための情報入力
server_address = input("Type in the server's address to connect to: ")
server_port = 9001

# サーバへの接続
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Connecting to {} port {}'.format(server_address, server_port))

try:
    sock.connect((server_address, server_port))
except socket.error as err:
    print(err)
    sys.exit(1)

try:
    # ファイルと処理内容の入力
    filepath = input('Type in a file to upload: ')
    operation = input('Enter the operation (compress, resize, aspect_ratio, extract_audio, create_gif, create_webm): ')
    options = {}
    if operation == 'resize':
        options['width'] = input('Enter the width: ')
        options['height'] = input('Enter the height: ')
    elif operation == 'aspect_ratio':
        options['aspect_ratio'] = input('Enter the aspect ratio (e.g., 16:9): ')
    elif operation in ['create_gif', 'create_webm']:
        options['start_time'] = input('Enter the start time (in seconds): ')
        options['duration'] = input('Enter the duration (in seconds): ')

    # JSONデータの作成
    request_data = {
        'operation': operation,
        'options': options
    }
    json_data = json.dumps(request_data).encode('utf-8')

    # ファイルの読み込み
    with open(filepath, 'rb') as f:
        payload = f.read()

    # ヘッダの作成と送信
    filename = os.path.basename(filepath)
    media_type = filename.split('.')[-1]
    header = protocol_header(len(json_data), len(media_type), len(payload))

    sock.send(header)
    sock.send(json_data)
    sock.send(media_type.encode('utf-8'))
    sock.send(payload)

    # サーバからの応答の受信
    response_header = sock.recv(8)
    json_length = int.from_bytes(response_header[:2], "big")
    media_type_length = int.from_bytes(response_header[2:3], "big")
    payload_length = int.from_bytes(response_header[3:8], "big")

    if json_length > 0:
        error_message = sock.recv(json_length).decode('utf-8')
        print('Error:', error_message)
    else:
        media_type = sock.recv(media_type_length).decode('utf-8')
        response_data = sock.recv(payload_length)
        output_file = 'output.' + media_type
        with open(output_file, 'wb') as f:
            f.write(response_data)
        print('Received processed file:', output_file)

finally:
    print('Closing socket')
    sock.close()
