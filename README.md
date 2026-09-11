 # 启动服务
  cd ~/data/python/CapsWriter-Offline
  nohup .venv/bin/python core_server.py >> /tmp/capswriter-server.log 2>&1 &

  （也可能多开过一次，日志在 /tmp/capswriter-server.log。）

  ────────────────────────────────────────

  停止服务端

  1. 按进程名停（最常用）

  pkill -f '/CapsWriter-Offline/.venv/bin/python core_server.py'

  或先看再杀：

  pgrep -af core_server
  kill <PID>          # 把上面看到的 PID 换掉
  # 还不退就：kill -9 <PID>

  2. 看 6016 端口是谁在听

  ss -tlnp | grep 6016
  # 或
  lsof -i :6016

  再 kill 对应 PID。

  3. 若装过 systemd 用户服务（跑过 ./create_autostart_linux.sh）

  systemctl --user stop capswriter-server capswriter-client
  # 不想开机自启：
  systemctl --user disable capswriter-server capswriter-client

  ────────────────────────────────────────

  客户端也要停的话

  pkill -f '/CapsWriter-Offline/.venv/bin/python core_client.py'
  # 或
  systemctl --user stop capswriter-client

  ────────────────────────────────────────

  注意： 在 SSH 里别用太宽的 pkill -f core_server.py，有时会把当前 shell 命令行一起匹配到。用上面带 .venv/bin/python core_server 的路径更稳。


