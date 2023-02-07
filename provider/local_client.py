# Echo client program
import socket

HOST = 'localhost'
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    code = "a=7\nprint(a)\na + 4"
    s.sendall(code.encode())
    data = s.recv(1024)
print('Received', repr(data))
