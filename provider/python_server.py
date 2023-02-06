import subprocess

from simple_client import SimpleClient

KERNEL_NAME = 'python3'

def start_kernel():
    cmd = ["jupyter", "kernel", "--kernel", KERNEL_NAME]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)

    proc.stderr.readline()
    line = proc.stderr.readline()
    connection_file_name = line.decode().strip().split()[3]
    return connection_file_name


connection_file_name = start_kernel()
c = SimpleClient(connection_file_name)

print(c.execute('a = "AAAAAAAA"'))
print(c.execute('a'))
print(c.execute('print(a)'))
print(c.execute('print(a)\na'))
print(c.execute('print("ZZ")\n1/0')['stdout'])
print(c.execute('print("aa")\nfrom time import sleep\nsleep(2)\nprint("bb")'))
