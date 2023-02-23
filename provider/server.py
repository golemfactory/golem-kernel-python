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
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(1)
            conn, addr = s.accept()

            connection_file_name = start_kernel()
            client = SimpleClient(connection_file_name)

            with conn:
                print('Connected by', addr)
                while True:
                    init_data = conn.recv(1024)

                    if not init_data:
                        break

                    message_len, data = init_data.split(b' ', maxsplit=1)
                    message_len = int(message_len.decode())

                    while len(data) < message_len:
                        data += conn.recv(1024)
                    
                    code = data.decode()
                    try:
                        result = client.execute(code)
                    except Exception as e:
                        #   I'm not sure if this can ever happen, but just in case
                        result = {'stdout': f"KERNEL CLIENT ERROR: {e}"}

                    data = json.dumps(result).encode()
                    bytes_len = len(data)
                    full_data = str(bytes_len).encode() + b' ' + data

                    conn.sendall(full_data)

# def run_server():
#     while True:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             s.bind((HOST, PORT))
#             s.listen(1)
#             conn, addr = s.accept()
# 
#             connection_file_name = start_kernel()
#             client = SimpleClient(connection_file_name)
# 
#             with conn:
#                 print('Connected by', addr)
#                 while True:
#                     init_data = conn.recv(1024)
# 
#                     if not init_data:
#                         break
# 
#                     message_len, data = init_data.split(b' ', maxsplit=1)
#                     message_len = int(message_len.decode())
# 
#                     while len(data) < message_len:
#                         data += conn.recv(1024)
# 
#                     code = "print('code!')"
# 
#                     try:
#                         result = client.execute(code)
#                     except Exception as e:
#                         #   I'm not sure if this can ever happen, but just in case
#                         result = {'stdout': f"KERNEL CLIENT ERROR: {e}"}
# 
#                     data = json.dumps(result).encode()
#                     bytes_len = len(data)
#                     full_data = str(bytes_len).encode() + b' ' + data
# 
#                     conn.sendall(full_data)

if __name__ == '__main__':
    run_server()
