from pexpect.replwrap import python
import sys

py = python()


def out(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()


while True:
    line = sys.stdin.readline().strip()
    py.run_command(line)
    if py.child.before:
        out(py.child.before)
    else:
        out("\n")
