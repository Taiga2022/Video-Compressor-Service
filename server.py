import socket
import os
import json
import subprocess
from pathlib import Path

# サーバの設定
server_address = '0.0.0.0'
server_port = 9001
dpath = 'temp'

# 一時ディレクトリの作成
if not os.path.exists(dpath):
    os.makedirs(dpath)

# サーバソケットの作成とバインド
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((server_address, server_port))
sock.listen(1)

print('Starting up on {} port {}'.format(server_address, server_port))

# 動画処理関数
def process_video(filepath, operation, options):
    output_file = os.path.join(dpath, 'output_' + os.path.basename(filepath))
    command = ['ffmpeg', '-y', '-i', filepath]

    if operation == 'compress':
        command.extend(['-vcodec', 'libx265', '-crf', '28', output_file])
    elif operation == 'resize':
        width, height = options['width'], options['height']
        command.extend(['-vf', f'scale={width}:{height}', output_file])
    elif operation == 'aspect_ratio':
        aspect_ratio = options['aspect_ratio']
        command.extend(['-vf', f'setdar={aspect_ratio}', output_file])
    elif operation == 'extract_audio':
        output_file = output_file.replace('.mp4', '.mp3')
        command.extend(['-q:a', '0', '-map', 'a', output_file])
    elif operation == 'create_gif':
        start_time, duration = options['start_time'], options['duration']
        output_file = output_file.replace('.mp4', '.gif')
        command.extend(['-ss', start_time, '-t', duration, '-vf', 'fps=10,scale=320:-1:flags=lanczos', output_file])
    elif operation == 'create_webm':
        start_time, duration = options['start_time'], options['duration']
        output_file = output_file.replace('.mp4', '.webm')
        command.extend(['-ss', start_time, '-t', duration, '-c:v', 'libvpx-vp9', '-b:v', '1M', output_file])

    subprocess.run(command)
    return output_file

# クライアント接続の待ち受け
while True:
    connection, client_address = sock.accept()
    try:
        print('Connection from', client_address)

        # ヘッダの受信
        header = connection.recv(8)
        json_length = int.from_bytes(header[:2], "big")
        media_type_length = int.from_bytes(header[2:3], "big")
        payload_length = int.from_bytes(header[3:8], "big")

        # JSONデータの受信
        json_data = connection.recv(json_length).decode('utf-8')
        request_data = json.loads(json_data)

        # メディアタイプの受信
        media_type = connection.recv(media_type_length).decode('utf-8')

        # ペイロードの受信
        input_file = os.path.join(dpath, 'input.' + media_type)
        with open(input_file, 'wb') as f:
            remaining = payload_length
            while remaining > 0:
                chunk_size = 4096 if remaining > 4096 else remaining
                chunk = connection.recv(chunk_size)
                if not chunk:
                    raise Exception('Connection lost while receiving the file.')
                f.write(chunk)
                remaining -= len(chunk)

        # リクエストの処理
        operation = request_data['operation']
        options = request_data['options']
        output_file = process_video(input_file, operation, options)

        # 処理結果の送信
        with open(output_file, 'rb') as f:
            output_data = f.read()

        response_header = (0).to_bytes(2, "big") + (len(media_type)).to_bytes(1, "big") + (len(output_data)).to_bytes(5, "big")
        connection.send(response_header)
        connection.send(media_type.encode('utf-8'))
        connection.send(output_data)

        print('Finished processing and sending the file to client.')

    except Exception as e:
        print('Error:', str(e))
        error_response = json.dumps({'error': str(e), 'solution': 'Check the request and try again.'}).encode('utf-8')
        error_header = (len(error_response)).to_bytes(2, "big") + (0).to_bytes(1, "big") + (0).to_bytes(5, "big")
        connection.send(error_header)
        connection.send(error_response)

    finally:
        print("Closing current connection")
        connection.close()
