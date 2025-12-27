import socket
import sys
import os

# サーバーのアドレスを設定
TCP_ADDRESS = ('localhost', 8080)
# 1. ソケットを作る（サーバーと同じ）
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.connect(TCP_ADDRESS)
print(f"サーバーに接続しました: {TCP_ADDRESS}")

# cliのコマンドからパス取得
file_path = sys.argv[1]
file_size = os.path.getsize(file_path)
ext = os.path.splitext(file_path)
if ext[1] != '.mp4':
    print("拡張子が異なります")
    exit()

# ファイルサイズをまず送る
tcp_sock.send(file_size.to_bytes(32, 'big'))

# withでファイルを「安全に」開閉する
try:
    with open(file_path, 'rb') as f:
        while True:
            # TCPのプロトコルのセグメントは最大1460なので1400で安定して送る
            chunk = f.read(1400)
            if not chunk:
                break
            tcp_sock.send(chunk)
    # 送信成功した場合のみレスポンス受信
    response = tcp_sock.recv(16)
    print(f"Server response: {response.decode('utf-8')}")
except Exception as e:
    print(f"処理エラー: {e}")

finally:
    # 最後に接続を閉じる
    tcp_sock.close()
