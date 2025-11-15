import socket
import os
import json
import math
from typing import Dict, Any, Callable, List

# TCP/IPのソケット(通信あり)を用意
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

# サーバが接続を待ち受けるUNIXドメインソケットのパスを指定します。
address = '/rpc_socket_file'

try:
    # もし前回の実行でソケットファイルが残っていた場合、そのファイルを削除します。
    os.unlink(address)
except FileNotFoundError:
    # ファイルが存在しない場合は何もしません。
    pass

# ソケットが起動していることを表示します。
print('starting up on {}'.format(address))

# sockオブジェクトのbindメソッドを使って、ソケットを特定のアドレスに関連付けます。
# socketファイルはserver側にあるためserverでbindする
sock.bind(address)

# ソケットが接続要求を待機するようにします
sock.listen(1)

"""10進数xを最も近い整数に切り捨て"""
def floor(x: float) -> int:
    return math.floor(x)

"""方程式 r^n = x における、rの値を計算"""
def nroot(n: int, x: int) -> float:
    return x ** (1 / n)

"""文字列sを入力として受け取り、入力文字列の逆である新しい文字列を返す"""
def reverse(s: str) -> str:
    return s[::-1]

"""2つの文字列を入力として受け取り、2つの入力文字列が互いにアナグラムであるかどうかを示すブール値を返す"""
def validAnagram(str1: str, str2: str) -> bool:
    return sorted(str1) == sorted(str2)

"""文字列の配列を入力として受け取り、その配列をソートして、ソート後の文字列の配列を返す"""
def sort(strArr: List[str]) -> List[str]:
    return sorted(strArr)

# 2. 関数マッピングの作成
def get_function_map() -> Dict[str, Callable]:
    # 辞書を返す
    return {
        'floor': floor,
        'nroot': nroot,
        'reverse': reverse,
        'validAnagram': validAnagram,
        'sort': sort
    }

# 3. レスポンス送信
def send_response(connection, response: Dict[str, Any]) -> None:
    """レスポンスを送信"""
    json_response = json.dumps(response).encode('utf-8')
    connection.send(json_response)
    print(f'📤 送信: {response}')

def send_error(connection, error_message: str, request_id: int) -> None:
    """エラーレスポンスを送信"""
    error_response = {
        "error": error_message,
        "id": request_id
    }
    send_response(connection, error_response)

# 4. リクエスト処理
def handle_request(connection, data: bytes) -> None:
    """リクエストを処理"""
    request_id = 0

    try:
        request = json.loads(data.decode('utf-8'))
        print(f'📥 受信: {request}')

        request_method = request['method']
        request_id = request.get('id', 0)

        # 関数マッピングから関数を取得
        function_map = get_function_map()

        # メソッドが存在するか確認
        if request_method not in function_map:
            send_error(connection, f"Unknown method: {request_method}", request_id)
            return

        function = function_map[request_method]

        # 関数を実行 (*でparams[]の中身を展開して渡す)
        result = function(*request['params'])

        # 結果の型を判定
        result_type = type(result).__name__
        if result_type == 'list':
            result_type = 'string[]'
        elif result_type == 'float':
            result_type = 'double'
        elif result_type == 'bool':
            result_type = 'boolean'

        response = {
            "results": str(result),
            "result_type": result_type,
            "id": request_id
        }

        # 🔧 修正: connectionを渡す
        send_response(connection, response)

    except KeyError as e:
        send_error(connection, f"Missing key: {e}", request_id)
    except Exception as e:
        send_error(connection, f"Server error: {e}", request_id)

# ソケットはデータの受信を永遠に待ち続けます。
while True:
    print('\nwaiting to receive message')
    connection, client_address = sock.accept()

    try:
        print(f'✅ connection from {client_address}')

        while True:
            data = connection.recv(4096)

            if data:
                handle_request(connection, data)
            else:
                print('📪 no more data')
                break

    finally:
        connection.close()
        print('🔒 connection closed')
