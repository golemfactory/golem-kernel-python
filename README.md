# This is a WIP of Jupyter Kernel notebook

## Installation

```
python3 -m pip install -U pip
python3 -m pip install -r requirements.txt
```

## Running Jupyter Notebook

```
python3 -m jupyter notebook
```
or just
```
jupyter notebook
```

## Description

### Which file does what

- **[Untitled.ipynb](Untitled.ipynb)** - an example notebook file that can be opened in jupyter and executed.
Right now it's demonstrating that our custom kernel echoing back the command being sent. 
- **[repl.py](repl.py)** - a script file that handles REPL functionality based on STDIN and STDOUT
- **[kernel.py](kernel.py)** - an implementation of a custom kernel that has access to the cell content sent by the web
user to parse, but for now just echoes it back
- **[kernel.json](kernel.json)** - a kernel definition file that is used to add a custom kernel to the web interface
- **[golem_requestor.py](golem_requestor.py)** an initial (incorrect) attempt to create a service hosting a REPL on Golem
and communicating with it via STDIN and STDOUT