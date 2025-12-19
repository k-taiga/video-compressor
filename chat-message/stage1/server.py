import socket
import time

# DGRAM = UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# IPアドレス + ポート
server_address = ('localhost', 8080)
# socketにIPアドレスとポートをバインド
sock.bind(server_address)
# {client_address: last_active_time}
clients = {}

while True:
    print('\nwaiting to receive message')

    # ソケットからのデータを受信
    # 4096は一度に受信できる最大バイト数
    # data = [2][k][t][h][e][l][l][o] 1byte目が名前の長さ
    # 第二引数はクライアント側のIP + エフェメラルポート(OS自動割当の動的ポート)
    data, client_address = sock.recvfrom(4096)

    # clientの時間を記憶
    clients[client_address] = time.time()

    # parse処理
    username_length = data[0]
    # username_lengthが2だとしたら1~3までスライス,3以降をスライス
    username = data[1:username_length+1]
    message = data[username_length+1:]

    # for k, v in clients.items() どこから取るか
    # k:v 何を入れるか
    # if どれを残すか
    # v > time.time() - 30 = 30秒以内のclients
    clients = {k : v for k, v in clients.items() if v > time.time() - 30}

    # 受信したデータのバイト数と送信元のアドレスを表示します。
    print('received {} bytes from {}'.format(len(data), client_address))
    print(data.decode('utf-8'))

    # 受信したデータをそのまま送信元に送り返します。
    if data:
        for client_addr in clients:
            sent = sock.sendto(data, client_addr)
            # 送信したバイト数と送信先のアドレスを表示します。
            print('sent {} bytes back to {}'.format(sent, client_address))