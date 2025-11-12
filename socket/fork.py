# osモジュールをインポートします。これには、システム固有のパラメータと関数が含まれています。
import os

# os.fork()を使用してプロセスを複製します。これは新しい「子プロセス」を作成します。
# fork()の戻り値は、親プロセスには新しく作成された子プロセスのプロセスID(PID)、子プロセスには0が返されます。
# os.fork()が呼び出されると、それまでの1つのプロセスが2つのプロセス（親プロセスと子プロセス）に分裂します。
# これら2つのプロセスはそれぞれ別々に、プログラムの残りの部分を実行します。
pid = os.fork()

# pidが0より大きい場合、これは親プロセスです。
if pid > 0:
    # os.getpid()は現在のプロセス(ここでは親プロセス)のPIDを返します。
    print("Fork above 0, PID:", os.getpid())

    # ここでは、生成された子プロセスのPIDを表示します。
    print("Spawned child's PID:", pid)

# pidが0の場合、これは子プロセスです。
else:
    # os.getpid()は現在のプロセス(ここでは子プロセス)のPIDを返します。
    print("Fork is 0, this is a Child PID:", os.getpid())

    # os.getppid()は現在のプロセスの親プロセスのPIDを返します。
    print("Parent PID:", os.getppid())