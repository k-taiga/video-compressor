# ============================================
# クライアント: ステージ2 チャットルームシステム
# ============================================

import socket
import threading
import sys

# --------------------------------------------------
# 初期設定
# --------------------------------------------------
# サーバーのアドレスを設定（TCP用とUDP用）
TCP_ADDRESS = ('localhost', 8080)
UDP_ADDRESS = ('localhost', 8081)

# トークンを保存する変数を用意
token = None
# ルーム名を保存する変数を用意
room_name = None
# ユーザー名を保存する変数を用意
username = None
# 終了フラグ
running = True

# --------------------------------------------------
# Step 1: ユーザーに選択させる
# --------------------------------------------------
print("=== チャットルームシステム ===")
print("1: 新しいチャットルームを作成")
print("2: 既存のチャットルームに参加")

choice = input("選択してください (1/2): ").strip()
while choice not in ['1', '2']:
    choice = input("1または2を入力してください: ").strip()

operation = int(choice)

# ユーザー名を入力させる
username = input("ユーザー名を入力してください: ").strip()
while not username:
    username = input("ユーザー名を入力してください: ").strip()

# ルーム名を入力させる
room_name = input("ルーム名を入力してください: ").strip()
while not room_name:
    room_name = input("ルーム名を入力してください: ").strip()

# --------------------------------------------------
# Step 2: TCPソケットを作成してサーバーに接続
# --------------------------------------------------
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.connect(TCP_ADDRESS)
print(f"サーバーに接続しました: {TCP_ADDRESS}")

# --------------------------------------------------
# Step 3: TCPヘッダー（32バイト）を組み立てる
# --------------------------------------------------
room_name_bytes = room_name.encode('utf-8')
payload_bytes = username.encode('utf-8')

# RoomNameSize: ルーム名のバイト数（1バイト）
room_name_size = len(room_name_bytes)
# Operation: 1=作成, 2=参加（1バイト）
# State: 0=リクエスト（1バイト）
state = 0
# OperationPayloadSize: ペイロードのバイト数（29バイト）
operation_payload_size = len(payload_bytes)

# ヘッダーを組み立て（32バイト）
header = bytes([room_name_size, operation, state])
header += operation_payload_size.to_bytes(29, 'big')

# --------------------------------------------------
# Step 4: TCPボディを組み立てる
# --------------------------------------------------
# ルーム名（UTF-8エンコード）
# ペイロード（ユーザー名など、UTF-8エンコード）
body = room_name_bytes + payload_bytes

# --------------------------------------------------
# Step 5: TCPでリクエストを送信（State=0）
# --------------------------------------------------
tcp_sock.send(header + body)
print("リクエストを送信しました")

# --------------------------------------------------
# Step 6: TCPで応答を受信（State=1）
# --------------------------------------------------
response = tcp_sock.recv(1)
status_code = response[0]

if status_code != 0:
    if operation == 1:
        print("エラー: ルームは既に存在します")
    else:
        print("エラー: ルームが見つかりません")
    tcp_sock.close()
    sys.exit(1)

print("リクエストが承認されました")

# --------------------------------------------------
# Step 7: TCPでトークンを受信（State=2）
# --------------------------------------------------
# トークンサイズ（1バイト）+ トークン
token_size_byte = tcp_sock.recv(1)
token_size = token_size_byte[0]
token = tcp_sock.recv(token_size).decode('utf-8')
print(f"トークンを受信しました: {token[:8]}...")

# TCP接続を閉じる
tcp_sock.close()
print("TCP接続を閉じました")

# --------------------------------------------------
# Step 8: UDPソケットを作成
# --------------------------------------------------
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# クライアント側もポートをバインド（受信用）
udp_sock.bind(('', 0))  # OSが空いているポートを割り当てる
print(f"UDPソケットを作成しました: {udp_sock.getsockname()}")

def build_udp_message(message_text):
    """UDPメッセージを組み立てる"""
    # --------------------------------------------------
    # Step 9: UDPヘッダー（2バイト）を組み立てる
    # --------------------------------------------------
    room_name_bytes = room_name.encode('utf-8')
    token_bytes = token.encode('utf-8')
    message_bytes = message_text.encode('utf-8')

    # RoomNameSize: ルーム名のバイト数（1バイト）
    room_name_size = len(room_name_bytes)
    # TokenSize: トークンのバイト数（1バイト）
    token_size = len(token_bytes)

    header = bytes([room_name_size, token_size])

    # --------------------------------------------------
    # Step 10: UDPボディを組み立てる
    # --------------------------------------------------
    # ルーム名（UTF-8エンコード）
    # トークン（UTF-8エンコード）
    # メッセージ（UTF-8エンコード）
    body = room_name_bytes + token_bytes + message_bytes

    return header + body

def parse_udp_message(data):
    """受信したUDPメッセージをパースする"""
    # 切断メッセージのチェック
    try:
        if data == b'HOST_DISCONNECTED':
            return None, None, "HOST_DISCONNECTED"
    except:
        pass

    room_name_size = data[0]
    token_size = data[1]

    offset = 2
    recv_room_name = data[offset:offset + room_name_size].decode('utf-8')
    offset += room_name_size

    recv_token = data[offset:offset + token_size].decode('utf-8')
    offset += token_size

    message = data[offset:].decode('utf-8')

    return recv_room_name, recv_token, message

# --------------------------------------------------
# Step 11: 送信スレッドと受信スレッドを作成
# --------------------------------------------------
def send_thread():
    """送信スレッド: ユーザー入力 → UDPで送信"""
    global running

    # --------------------------------------------------
    # Step 12: メッセージ送信ループ
    # --------------------------------------------------
    print("\n=== チャット開始 ===")
    print("メッセージを入力してください（/exit で終了）:")

    while running:
        try:
            message = input()
            if not running:
                break

            if message == "/exit":
                # 終了メッセージを送信
                udp_data = build_udp_message("/exit")
                udp_sock.sendto(udp_data, UDP_ADDRESS)
                running = False
                print("チャットを終了します")
                break

            # ヘッダー + ボディを組み立てる
            udp_data = build_udp_message(f"{username}: {message}")
            # sendto() でサーバーに送信
            udp_sock.sendto(udp_data, UDP_ADDRESS)

        except EOFError:
            running = False
            break
        except Exception as e:
            if running:
                print(f"送信エラー: {e}")

def recv_thread():
    """受信スレッド: UDPで受信 → 画面に表示"""
    global running

    # --------------------------------------------------
    # Step 13: メッセージ受信ループ
    # --------------------------------------------------
    while running:
        try:
            udp_sock.settimeout(1.0)  # タイムアウトを設定
            data, addr = udp_sock.recvfrom(4096)

            recv_room, recv_token, message = parse_udp_message(data)

            # 切断メッセージを受信したら終了
            if message == "HOST_DISCONNECTED":
                print("\nホストが退出したため、チャットが終了しました")
                running = False
                break

            # 自分のメッセージは表示しない（トークンで判定）
            if recv_token != token:
                print(f"\r{message}")
                print("", end="", flush=True)

        except socket.timeout:
            continue
        except Exception as e:
            if running:
                pass  # タイムアウト以外のエラーは無視

# スレッドを作成して開始
sender = threading.Thread(target=send_thread, daemon=True)
receiver = threading.Thread(target=recv_thread, daemon=True)

sender.start()
receiver.start()

# メインスレッドで送信スレッドの終了を待つ
sender.join()

# --------------------------------------------------
# Step 14: 終了処理
# --------------------------------------------------
running = False
udp_sock.close()
print("ソケットを閉じました")
