### Interactive Python shell

#### Prerequisites
* Python 3.8
* Installed `requirements.txt`

#### Usage

Run the server: 
```shell
$ python shell.py run
Spawning Python subprocess...
Forwarding input from ipc:///tmp/shell_input.sock...
Forwarding output to ipc:///tmp/shell_output.sock...
```

Write to stdin:
```shell
$ echo "print('test')" | python shell.py write
```

Read one line from stdout:
```shell
$ python shell.py read
test
>>>
```

If not output is available, `read` command will wait indefinitely.
If the Python shell has exited it will exit without printing anything.

Run full interactive shell:
```shell
$ ./run_shell.sh 
>>> x = 1
>>> x
1
>>> x += 2
>>> x
3
>>> exit()
```
