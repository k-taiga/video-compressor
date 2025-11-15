import socket
import os
import json
from typing import Any, List, Dict

# TCP/IPのソケット(通信あり)を用意
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

# サーバのアドレスを定義します。
address = '/rpc_socket_file'

print(f'🔌 サーバに接続中: {address}')
try:
    sock.connect(address)
    print('✅ 接続完了\n')
except FileNotFoundError:
    print(f'❌ エラー: サーバーが起動していません')
    print(f'   先にサーバーを起動してください: python3 rpc/rpc-server.py')
    exit(1)

"""
RPC関数を呼び出すヘルパー関数

Args:
    method: 呼び出すメソッド名
    params: パラメータのリスト
    param_types: パラメータの型のリスト
    request_id: リクエストID

Returns:
    サーバからのレスポンス(辞書形式)
"""
def call_rpc(
    method: str,
    params: List[Any],
    param_types: List[str],
    request_id: int = 1
) -> Dict[str, Any]:
    # リクエストを作成
    request = {
        "method": method,
        "params": params,
        "param_types": param_types,
        "id": request_id
    }

    # JSON文字列に変換してバイト列にエンコード
    message = json.dumps(request).encode('utf-8')

    # サーバにメッセージを送信
    print(f'📤 送信: {request}')
    sock.send(message)

    # サーバからの応答を待ち受け
    print('⏳ レスポンス待機中...')
    # 🔧 修正: recvfrom() → recv() に変更
    data = sock.recv(4096)

    # 受信したデータをJSON形式に変換
    response = json.loads(data.decode('utf-8'))
    print(f'📥 受信: {response}\n')

    return response

try:
    print("=" * 50)
    print("🎯 RPCクライアント")
    print("=" * 50)
    print("\n利用可能な関数:")
    print("1. floor(double x) - 小数を切り捨て")
    print("2. nroot(int n, int x) - n乗根を計算")
    print("3. reverse(string s) - 文字列を反転")
    print("4. validAnagram(string str1, string str2) - アナグラム判定")
    print("5. sort(string[] strArr) - 文字列配列をソート")
    print("0. 終了")

    request_id = 1

    while True:
        choice = input("\n関数を選択してください (0-5): ")

        if choice == "0":
            print("👋 終了します")
            break
        elif choice == "1":
            x = float(input("小数を入力してください: "))
            response = call_rpc("floor", [x], ["double"], request_id)
            if "error" in response:
                print(f"❌ エラー: {response['error']}")
            else:
                print(f"✅ 結果: {response['results']}")
        elif choice == "2":
            n = int(input("n(乗数)を入力してください: "))
            x = int(input("x(値)を入力してください: "))
            response = call_rpc("nroot", [n, x], ["int", "int"], request_id)
            if "error" in response:
                print(f"❌ エラー: {response['error']}")
            else:
                print(f"✅ 結果: {response['results']}")
        elif choice == "3":
            s = input("文字列を入力してください: ")
            response = call_rpc("reverse", [s], ["string"], request_id)
            if "error" in response:
                print(f"❌ エラー: {response['error']}")
            else:
                print(f"✅ 結果: {response['results']}")
        elif choice == "4":
            str1 = input("1つ目の文字列を入力してください: ")
            str2 = input("2つ目の文字列を入力してください: ")
            response = call_rpc("validAnagram", [str1, str2], ["string", "string"], request_id)
            if "error" in response:
                print(f"❌ エラー: {response['error']}")
            else:
                print(f"✅ 結果: {response['results']}")
        elif choice == "5":
            arr_input = input("文字列をカンマ区切りで入力してください: ")
            arr = [s.strip() for s in arr_input.split(",")]
            response = call_rpc("sort", [arr], ["string[]"], request_id)
            if "error" in response:
                print(f"❌ エラー: {response['error']}")
            else:
                print(f"✅ 結果: {response['results']}")
        else:
            print("❌ 無効な選択です")
            continue

        request_id += 1

except KeyboardInterrupt:
    print("\n\n👋 Ctrl+Cで終了します")
except Exception as e:
    print(f"\n❌ エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()

finally:
    # 最後にソケットを閉じてリソースを解放します
    print('\n🔒 ソケットをクローズします')
    sock.close()
