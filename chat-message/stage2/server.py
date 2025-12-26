import socket
import threading
import secrets
import time

# TCPソケットとUDPソケットを作成
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# それぞれのポートにbind
tcp_address = ('localhost', 8080)
udp_address = ('localhost', 8081)
# socketにIPアドレスとポートをバインド
tcp_sock.bind(tcp_address)
# tcpは待ち受ける数を指定する
tcp_sock.listen(5)
udp_sock.bind(udp_address)

# チャットルームを管理する辞書を用意 {room_name: {host_token, tokens: {token: ip_address}, clients: {address: last_active}}}
chat_rooms = {}
# スレッドセーフのためのロック
rooms_lock = threading.Lock()

def generate_token():
    """ユニークなトークンを生成"""
    return secrets.token_hex(16)

def handle_tcp():
    while True:
        # 接続を受け付ける tcpではbind→listen→accept→recvという手順が必要
        client_socket, client_address = tcp_sock.accept()
        print(f"TCP接続: {client_address}")

        try:
            # --------------------------------------------------
            # Step 2: TCP - ヘッダー（32バイト）をパースする
            # --------------------------------------------------
            header = client_socket.recv(32)
            if len(header) < 32:
                client_socket.close()
                continue

            room_name_size = header[0]
            operation = header[1]
            state = header[2]
            # OperationPayloadSizeは29バイト（ヘッダーの残り）
            operation_payload_size = int.from_bytes(header[3:32], 'big')

            # --------------------------------------------------
            # Step 3: TCP - ボディをパースする
            # --------------------------------------------------
            # RoomNameSizeバイト分を読んでルーム名を取得
            room_name_bytes = client_socket.recv(room_name_size)
            room_name = room_name_bytes.decode('utf-8')

            # OperationPayloadSizeバイト分を読んでペイロード（ユーザー名など）を取得
            if operation_payload_size > 0:
                payload_bytes = client_socket.recv(operation_payload_size)
                payload = payload_bytes.decode('utf-8')
            else:
                payload = ""

            print(f"ルーム名: {room_name}, Operation: {operation}, State: {state}, ペイロード: {payload}")

            # --------------------------------------------------
            # Step 4: TCP - 部屋の作成処理（Operation=1）
            # --------------------------------------------------
            if operation == 1:
                with rooms_lock:
                    # ルーム名が既に存在するかチェック
                    if room_name in chat_rooms:
                        # State=1: ステータスコード（失敗）を含む応答を送信
                        response = bytes([1])  # 1 = 失敗（ルームが既に存在）
                        client_socket.send(response)
                        client_socket.close()
                        continue

                    # State=1: ステータスコード（成功）を含む応答を送信
                    response = bytes([0])  # 0 = 成功
                    client_socket.send(response)

                    # トークンを生成（ユニークな文字列）
                    token = generate_token()

                    # ルーム情報を辞書に保存（ホストとして登録）
                    chat_rooms[room_name] = {
                        'host_token': token,
                        'host_name': payload,
                        'tokens': {token: client_address[0]},
                        'clients': {}  # {address: {'last_active': timestamp, 'token': token, 'username': name}}
                    }

                    # State=2: トークンをクライアントに送信
                    token_bytes = token.encode('utf-8')
                    # トークンサイズ（1バイト）+ トークン
                    client_socket.send(bytes([len(token_bytes)]) + token_bytes)
                    print(f"ルーム '{room_name}' を作成しました。トークン: {token}")

            # --------------------------------------------------
            # Step 5: TCP - 部屋への参加処理（Operation=2）
            # --------------------------------------------------
            elif operation == 2:
                with rooms_lock:
                    # ルーム名が存在するかチェック
                    if room_name not in chat_rooms:
                        # State=1: ステータスコード（失敗）を含む応答を送信
                        response = bytes([1])  # 1 = 失敗（ルームが存在しない）
                        client_socket.send(response)
                        client_socket.close()
                        continue

                    # State=1: ステータスコード（成功）を含む応答を送信
                    response = bytes([0])  # 0 = 成功
                    client_socket.send(response)

                    # トークンを生成（ユニークな文字列）
                    token = generate_token()

                    # ルーム情報にトークンを追加（ゲストとして登録）
                    chat_rooms[room_name]['tokens'][token] = client_address[0]

                    # State=2: トークンをクライアントに送信
                    token_bytes = token.encode('utf-8')
                    # トークンサイズ（1バイト）+ トークン
                    client_socket.send(bytes([len(token_bytes)]) + token_bytes)
                    print(f"ユーザー '{payload}' がルーム '{room_name}' に参加しました。トークン: {token}")

            # TCP接続を閉じる
            client_socket.close()

        except Exception as e:
            print(f"TCP処理エラー: {e}")
            client_socket.close()

def handle_udp():
    while True:
        # データと送信元アドレスを受信
        # udpはrecvfrom必要
        data, client_address = udp_sock.recvfrom(4096)
        print(f"UDP受信: {client_address}")

        try:
            # --------------------------------------------------
            # Step 6: UDP - ヘッダー（2バイト）をパースする
            # --------------------------------------------------
            if len(data) < 2:
                continue

            room_name_size = data[0]
            token_size = data[1]

            # --------------------------------------------------
            # Step 7: UDP - ボディをパースする
            # --------------------------------------------------
            offset = 2
            # RoomNameSizeバイト分を読んでルーム名を取得
            room_name = data[offset:offset + room_name_size].decode('utf-8')
            offset += room_name_size

            # TokenSizeバイト分を読んでトークンを取得
            token = data[offset:offset + token_size].decode('utf-8')
            offset += token_size

            # 残りをメッセージとして取得
            message = data[offset:].decode('utf-8')

            print(f"ルーム: {room_name}, トークン: {token[:8]}..., メッセージ: {message}")

            # --------------------------------------------------
            # Step 8: UDP - トークンとIPアドレスの検証
            # --------------------------------------------------
            with rooms_lock:
                # ルームが存在するか確認
                if room_name not in chat_rooms:
                    print(f"ルーム '{room_name}' が存在しません")
                    continue

                room = chat_rooms[room_name]

                # トークンがルームに登録されているか確認
                if token not in room['tokens']:
                    print(f"無効なトークン: {token[:8]}...")
                    continue

                # トークンに紐づくIPアドレスと送信元IPが一致するか確認
                registered_ip = room['tokens'][token]
                sender_ip = client_address[0]

                # localhostの場合は127.0.0.1として扱う
                if registered_ip == 'localhost':
                    registered_ip = '127.0.0.1'
                if sender_ip == 'localhost':
                    sender_ip = '127.0.0.1'

                # IPアドレスの検証（開発環境ではlocalhostなので緩和）
                # 本番環境では厳密にチェックすべき
                # if registered_ip != sender_ip:
                #     print(f"IPアドレス不一致: 登録={registered_ip}, 送信元={sender_ip}")
                #     continue

                # --------------------------------------------------
                # Step 9: UDP - メッセージのリレー
                # --------------------------------------------------
                # クライアントの最終アクティブ時間を更新
                current_time = time.time()
                room['clients'][client_address] = {
                    'last_active': current_time,
                    'token': token
                }

                # 30秒以上非アクティブなクライアントを削除
                inactive_clients = []
                for addr, info in room['clients'].items():
                    if current_time - info['last_active'] > 30:
                        inactive_clients.append(addr)

                for addr in inactive_clients:
                    del room['clients'][addr]
                    print(f"非アクティブなクライアントを削除: {addr}")

                # --------------------------------------------------
                # Step 10: ホスト退出時の処理
                # --------------------------------------------------
                # ホストが退出したらルームを削除
                if token == room['host_token'] and message == "/exit":
                    # ルーム内の全クライアントに切断メッセージを送信
                    disconnect_msg = "HOST_DISCONNECTED".encode('utf-8')
                    for addr in room['clients']:
                        if addr != client_address:
                            udp_sock.sendto(disconnect_msg, addr)

                    del chat_rooms[room_name]
                    print(f"ホストが退出したためルーム '{room_name}' を削除しました")
                    continue

                # ルーム内の全クライアントにメッセージを転送
                relay_message = data  # 元のデータをそのまま転送
                for addr in room['clients']:
                    if addr != client_address:  # 送信者以外に転送
                        udp_sock.sendto(relay_message, addr)
                        print(f"メッセージを転送: {addr}")

        except Exception as e:
            print(f"UDP処理エラー: {e}")

# threadを分けて処理待ち targetが処理するメソッド
tcp_thread = threading.Thread(target=handle_tcp, daemon=True)
tcp_thread.start()
udp_thread = threading.Thread(target=handle_udp, daemon=True)
udp_thread.start()

print("サーバーが起動しました")
print(f"TCP: {tcp_address}")
print(f"UDP: {udp_address}")

# メインスレッドを維持
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nサーバーを終了します")
    tcp_sock.close()
    udp_sock.close()
