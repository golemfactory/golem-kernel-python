FROM python:3.8-slim
WORKDIR /python_shell

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt
RUN rm requirements.txt

COPY shell.py .
