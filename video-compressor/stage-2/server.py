import os
import socket
import json
import time
from protocol import parse_header, HEADER_SIZE, create_header
import subprocess

TCP_ADDRESS = ('localhost', 8080)


def create_server_socket() -> socket.socket:
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(TCP_ADDRESS)
    server_sock.listen(5)
    print(f"サーバー起動: {TCP_ADDRESS}")
    return server_sock


def receive_header(client_sock: socket.socket) -> tuple[int, int, int]:
    # ヘッダー受信(8バイト目までがheader)
    header = client_sock.recv(HEADER_SIZE)
    # parseして中身を取得
    return parse_header(header)


def receive_json(client_sock: socket.socket, json_size: int) -> dict:
    # JSON受信(headerのbyteの数)
    json_bytes = client_sock.recv(json_size)
    request = json.loads(json_bytes.decode('utf-8'))
    print(f"リクエスト: {request}")
    return request


def receive_media_type(client_sock: socket.socket, media_type_size: int) -> str:
    # メディアタイプ受信(headerのbyteの数)
    media_type_bytes = client_sock.recv(media_type_size)
    media_type = media_type_bytes.decode('utf-8')
    print(f"メディアタイプ: {media_type}")
    return media_type


def receive_payload(client_sock: socket.socket, payload_size: int, media_type: str) -> str:
    # ペイロード受信 & 保存
    # fはformat文字列 "temp_" + str(timestamp) + "." + media_typeと同じ
    filename = f"temp_{int(time.time())}.{media_type}"
    received = 0
    with open(filename, 'wb') as f:
        while received < payload_size:
            # tcpの最大のバイトごとにchunkで取得
            # minで最後の残り少ない分はその分だけ取得
            chunk = client_sock.recv(min(1400, payload_size - received))
            if not chunk:
                break
            f.write(chunk)
            # receivedにいままで受信したbyte数を記載
            received += len(chunk)
    return filename


def process_video(operation: str, request: dict, filename: str, media_type: str) -> tuple[str, str]:
    # FFMPEG処理
    output_filename = f"output_{int(time.time())}"
    output_media_type = media_type

    match operation:
        # 圧縮 元と同じmedia_type
        case "compress":
            output_filename += f".{media_type}"
            # ffmpegの子プロセスを並列で起動
            # runのため自動でこの処理が終わるのを待機する
            subprocess.run([
                "ffmpeg", "-i", filename,
                "-crf", "23",
                output_filename
            ])
        # 解像度変更 元と同じmedia_type
        case "resolution":
            width = request["width"]
            height = request["height"]
            output_filename += f".{media_type}"
            subprocess.run([
                "ffmpeg", "-i", filename,
                "-vf", f"scale={width}:{height}",
                output_filename
            ])
        # アスペクト比変更 元と同じmedia_type
        case "aspect":
            aspect = request["aspect"]
            output_filename += f".{media_type}"
            subprocess.run([
                "ffmpeg", "-i", filename,
                "-aspect", aspect,
                output_filename
            ])
        # 音声抽出 mp3でmedia_type返す
        case "audio":
            output_media_type = "mp3"
            output_filename += ".mp3"
            subprocess.run([
                "ffmpeg", "-i", filename,
                "-vn",  # 映像を除去
                "-acodec", "libmp3lame",  # MP3エンコーダー
                output_filename
            ])
        # 切り取り変換 gifでmedia_type返す
        case "gif":
            output_media_type = "gif"
            start = request["start"]
            end = request["end"]
            duration = end - start
            output_filename += ".gif"
            subprocess.run([
                "ffmpeg", "-i", filename,
                "-ss", str(start),  # 開始位置
                "-t", str(duration),  # 長さ
                output_filename
            ])

        case _:
            print(f"不明な操作: {operation}")

    return output_filename, output_media_type


def send_response(client_sock: socket.socket, output_filename: str, output_media_type: str) -> None:
    # 結果をMMPで送信
    response = {"status": "success"}
    response_json = json.dumps(response).encode('utf-8')

    output_media_type_bytes = output_media_type.encode('utf-8')

    output_size = os.path.getsize(output_filename)

    response_header = create_header(
        len(response_json), len(output_media_type_bytes), output_size
    )

    client_sock.send(response_header)
    client_sock.send(response_json)
    client_sock.send(output_media_type_bytes)

    # ファイルを1400バイトずつ送信
    with open(output_filename, 'rb') as f:
        while True:
            chunk = f.read(1400)
            if not chunk:
                break
            client_sock.send(chunk)


def main() -> None:
    server_sock = create_server_socket()

    while True:
        client_sock, client_addr = server_sock.accept()
        print(f"接続: {client_addr}")

        try:
            json_size, media_type_size, payload_size = receive_header(client_sock)
            request = receive_json(client_sock, json_size)
            media_type = receive_media_type(client_sock, media_type_size)
            filename = receive_payload(client_sock, payload_size, media_type)

            operation = request["operation"]
            output_filename, output_media_type = process_video(operation, request, filename, media_type)

            send_response(client_sock, output_filename, output_media_type)

        except Exception as e:
            print(f"エラー: {e}")
        finally:
            client_sock.close()
            # 一時ファイル削除
            if os.path.exists(filename):
                os.remove(filename)
            if os.path.exists(output_filename):
                os.remove(output_filename)
            client_sock.close()


if __name__ == "__main__":
    main()
