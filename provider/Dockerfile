FROM python:3.8-slim

#   DEBUG
VOLUME /ttt 

WORKDIR /python_server

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt
RUN rm requirements.txt

COPY simple_client.py .
COPY python_server.py .
COPY example_client.py .
