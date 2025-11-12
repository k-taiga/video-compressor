import os

# os.pipe()は2つのファイル記述子を生成し、これらはパイプでつながれています。
# rは読み取り専用、wは書き込み専用
r, w = os.pipe()
pid = os.fork()

if pid > 0:
    # 親プロセスでは読み取り端を閉じます。
    # なぜなら、親プロセスはパイプにデータを書き込むだけで、読み取らないからです。
    os.close(r)
    # 親プロセスからのメッセージを生成します。
    # os.getpid()を使用して現在のプロセスID（親プロセスのID）を取得します。
    message = 'Message from parent with pid {}'.format(os.getpid())
    # 生成したメッセージを表示します。
    print("Parent, sending out the message - {}".format(message, os.getpid()))
    # メッセージをエンコードしてパイプに書き込みます。
    os.write(w, message.encode('utf_8'))

else:
    # 子プロセスでは書き込み端を閉じます。
    # なぜなら、子プロセスはパイプからデータを読み取るだけで、書き込まないからです。
    os.close(w)
    # 子プロセスであることとそのプロセスIDを表示します。
    print("Fork is 0, this is a Child PID:", os.getpid())
    # 読み取り用のファイルディスクリプタを開きます。
    f = os.fdopen(r)
    # パイプから読み取ったメッセージを表示します。
    print("Incoming string:", f.read())