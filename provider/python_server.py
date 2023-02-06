import subprocess

from flask import Flask, request

from simple_client import SimpleClient

app = Flask(__name__)

def start_kernel():
    cmd = ["jupyter", "kernel", "--kernel", "python3"]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)

    proc.stderr.readline()
    line = proc.stderr.readline()
    connection_file_name = line.decode().strip().split()[3]
    return connection_file_name


client = None
@app.before_first_request
def create_client():
    connection_file_name = start_kernel()
    global client
    client = SimpleClient(connection_file_name)


@app.route("/execute", methods=["POST"])
def execute():
    code = request.get_json(force=True)['code']
    return client.execute(code)
