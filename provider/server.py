import json
import socket
import subprocess

from simple_client import SimpleClient

HOST = ''
PORT = 5000


def start_kernel():
    cmd = ["/usr/src/app/workdir/venv/bin/jupyter", "kernel", "--kernel", "python3"]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)

    proc.stderr.readline()
    line = proc.stderr.readline()
    connection_file_name = line.decode().strip().split()[3]
    return connection_file_name


def get_code(conn):
    #   NOTE: Code is sent only after previous code was fully processed, so this simplified
    #         implementation should be OK - we never receive anything after the message_len.
    init_data = conn.recv(1024)

    if not init_data:
        return None

    message_len, data = init_data.split(b' ', maxsplit=1)
    message_len = int(message_len.decode())

    while len(data) < message_len:
        data += conn.recv(1024)

    return data.decode()


def send_result(conn, result):
    data = result.encode()
    bytes_len = len(data)
    full_data = str(bytes_len).encode() + b' ' + data

    conn.sendall(full_data)


def indicate_server_ready():
    with open('/usr/src/app/workdir/server_status.txt', 'w') as f:
        f.write('LOADED')


def indicate_kernel_ready():
    with open('/usr/src/app/workdir/kernel_status.txt', 'w') as f:
        f.write('LOADED')


def run_server():
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(1)
            indicate_server_ready()
            conn, addr = s.accept()

            connection_file_name = start_kernel()
            client = SimpleClient(connection_file_name)

            with conn:
                indicate_kernel_ready()
                while True:
                    code = get_code(conn)
                    if code is None:
                        break

                    try:
                        result = client.execute(code)
                    except Exception as e:
                        #   I'm not sure if this can ever happen, but just in case
                        result = {'stdout': f"KERNEL CLIENT ERROR: {e}"}

                    send_result(conn, json.dumps(result))


if __name__ == '__main__':
    run_server()
