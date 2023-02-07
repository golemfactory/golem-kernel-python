# Echo server program
import socket

import subprocess
import json

from simple_client import SimpleClient

HOST = ''
PORT = 5000

def start_kernel():
    cmd = ["jupyter", "kernel", "--kernel", "python3"]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)

    proc.stderr.readline()
    line = proc.stderr.readline()
    connection_file_name = line.decode().strip().split()[3]
    return connection_file_name

def run_server():
    connection_file_name = start_kernel()
    client = SimpleClient(connection_file_name)

    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(1)
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                while True:
                    code = conn.recv(1024).decode()
                    if not code:
                        break

                    result = client.execute(code)
                    conn.sendall(json.dumps(result).encode())


if __name__ == '__main__':
    run_server()
