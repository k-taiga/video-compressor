import socket

username_input = input("ユーザー名を入力してください: ")
message_input = input("メッセージを入力してください: ")

# messageとuser_nameをUTF-8のbyteに変換する
username = username_input.encode('utf-8')
message = message_input.encode('utf-8')
# UTF-8のバイト数(長さをバイト化する)を取得する
username_length = len(username).to_bytes(1, byteorder='big')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 8080)

try:
    data = username_length + username + message
    # エフェメラルポートで送信(ex. localhost:54321)
    sock.sendto(data, server_address)

    # サーバからの応答を待つ時間を2秒間に設定します。
    # この時間が過ぎても応答がない場合、プログラムは次のステップに進みます。
    sock.settimeout(2)

    # サーバからの応答を待ち、応答があればそれを表示します。
    try:
        while True:
            # サーバからのデータを受け取る
            # 第二引数でserver_address(localhost:8080)を受け取れるが使わないので破棄
            data, _ = sock.recvfrom(4096)

            # データがあればそれを表示し、なければループを終了します。
            if data:
                print('Server response: ' + data.decode('utf-8'))
            else:
                break

    # 2秒間サーバからの応答がなければ、タイムアウトエラーとなり、エラーメッセージを表示します。
    except TimeoutError:
        print('Socket timeout, ending listening for server messages')

# すべての操作が完了したら、最後にソケットを閉じて通信を終了します。
finally:
    print('closing socket')
    sock.close()