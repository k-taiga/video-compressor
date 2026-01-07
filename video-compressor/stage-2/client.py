import socket
import sys
import os
import json
import time
from protocol import create_header, parse_header, HEADER_SIZE

# サーバーのアドレスを設定
TCP_ADDRESS = ('localhost', 8080)


def get_file_info(file_path: str) -> tuple[int, str, bytes]:
    # ファイルサイズ取得
    payload_size = os.path.getsize(file_path)
    # メディアタイプ取得
    # .でわけて1の方を取得 [0: 'hoge' ,1: '.mp4']
    media_type = os.path.splitext(file_path)[1][1:]
    media_type_bytes = media_type.encode('utf-8')
    return payload_size, media_type, media_type_bytes


# **でどんなものでもdist(辞書形式 ex.{"a": 1, "b": 2})で受け取る
def create_request(operation: str, **kwargs) -> bytes:
    # JSON作成（操作を指定）
    request = {"operation": operation, **kwargs}
    return json.dumps(request).encode('utf-8')


def connect_to_server() -> socket.socket:
    # TCP接続
    # ソケットを作る
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(TCP_ADDRESS)
    print(f"サーバーに接続しました: {TCP_ADDRESS}")
    return sock


def send_request(sock: socket.socket, json_bytes: bytes, media_type_bytes: bytes, payload_size: int, file_path: str) -> None:
    # MMPヘッダー作成
    # 送信データ: [8バイト][JSONバイト][メディアタイプバイト][payloadのファイル]
    header = create_header(
        len(json_bytes),
        len(media_type_bytes),
        payload_size,
    )

    # ヘッダー、JSON、メディアタイプ送信
    sock.send(header)
    sock.send(json_bytes)
    sock.send(media_type_bytes)

    # ペイロード送信
    # withでファイルを「安全に」開閉する
    with open(file_path, 'rb') as f:
        while True:
            # TCPのプロトコルのセグメントは最大1460なので1400で安定して送る
            chunk = f.read(1400)
            if not chunk:
                break
            sock.send(chunk)


def receive_header(sock: socket.socket) -> tuple[int, int, int]:
    # ヘッダー受信（8バイト）
    response_header = sock.recv(HEADER_SIZE)
    return parse_header(response_header)


def receive_json(sock: socket.socket, json_size: int) -> dict:
    # JSON受信
    response_json = sock.recv(json_size)
    response = json.loads(response_json.decode('utf-8'))
    print(f"サーバーレスポンス: {response}")
    return response


def receive_media_type(sock: socket.socket, media_type_size: int) -> str:
    # メディアタイプ受信
    response_media_type = sock.recv(media_type_size).decode('utf-8')
    print(f"メディアタイプ: {response_media_type}")
    return response_media_type


def receive_payload(sock: socket.socket, payload_size: int, response_media_type: str) -> str:
    # ペイロード受信 & ファイル保存
    output_filename = f"downloaded_{int(time.time())}.{response_media_type}"
    received = 0
    with open(output_filename, 'wb') as f:
        while received < payload_size:
            # minで最後の残り少ない分はその分だけ取得
            chunk = sock.recv(min(1400, payload_size - received))
            if not chunk:
                break
            f.write(chunk)
            # receivedにいままで受信したbyte数を記載
            received += len(chunk)
    print(f"保存完了: {output_filename}")
    return output_filename


def parse_args() -> tuple[str, str, dict]:
    # 使い方を表示
    # python client.py <file_path> <operation> [options...]
    # operations:
    #   compress
    #   resolution <width> <height>
    #   aspect <aspect_ratio>
    #   audio
    #   gif <start> <end>
    if len(sys.argv) < 3:
        print("使い方: python client.py <file_path> <operation> [options...]")
        print("operations:")
        print("  compress")
        print("  resolution <width> <height>")
        print("  aspect <aspect_ratio>")
        print("  audio")
        print("  gif <start> <end>")
        sys.exit(1)

    file_path = sys.argv[1]
    operation = sys.argv[2]
    kwargs = {}

    match operation:
        case "compress" | "audio":
            pass
        case "resolution":
            kwargs["width"] = int(sys.argv[3])
            kwargs["height"] = int(sys.argv[4])
        case "aspect":
            kwargs["aspect"] = sys.argv[3]
        case "gif":
            kwargs["start"] = int(sys.argv[3])
            kwargs["end"] = int(sys.argv[4])
        case _:
            print(f"不明な操作: {operation}")
            sys.exit(1)

    return file_path, operation, kwargs


def main() -> None:
    file_path, operation, kwargs = parse_args()

    payload_size, media_type, media_type_bytes = get_file_info(file_path)
    json_bytes = create_request(operation, **kwargs)
    sock = connect_to_server()

    try:
        send_request(sock, json_bytes, media_type_bytes, payload_size, file_path)

        json_size, media_type_size, response_payload_size = receive_header(sock)
        receive_json(sock, json_size)
        response_media_type = receive_media_type(sock, media_type_size)
        receive_payload(sock, response_payload_size, response_media_type)

    except Exception as e:
        print(f"処理エラー: {e}")

    finally:
        # 最後に接続を閉じる
        sock.close()


if __name__ == "__main__":
    main()
