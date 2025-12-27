import socket
import time

# TCPソケットを作成(TCPは作成->bind->listen->accept
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_address = ('localhost', 8080)
# socketにIPアドレスとポートをバインド
tcp_sock.bind(tcp_address)
# tcpは待ち受ける数を指定する
tcp_sock.listen(5)

# tcpの処理
while True:
    # 接続を受け付ける tcpではbind→listen→accept→recvという手順が必要
    client_socket, client_address = tcp_sock.accept()
    print(f"TCP接続: {client_address}")
    try:
        # 最初のファイルのバイト数を取得
        file_size_data = client_socket.recv(32)
        if len(file_size_data) < 32:
            client_socket.close()
            continue
        file_size = int.from_bytes(file_size_data, 'big')
        print(f"ファイルサイズ: {file_size}")
        received = 0
        filename = f"{int(time.time())}.mp4"
        # 保存先を指定し書き込みモードで開く
        with open(filename, 'wb') as f:
            while received < file_size:
                data = client_socket.recv(1400)
                received += len(data)
                f.write(data)
        # 16バイトのメッセージを送る
        message = "success".ljust(16)
        client_socket.send(message.encode('utf-8'))
    except Exception as e:
        print(f"処理エラー: {e}")
    finally:
        # TCP接続を閉じる
        client_socket.close()