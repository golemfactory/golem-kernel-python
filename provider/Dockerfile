FROM python:3.8-slim

#   The only purpose of this VOLUME is development/debuging,
#   thanks to it we can send a new `server.py` or `simple_client.py` file
#   and avoid rebuilding images.
VOLUME /ttt 

WORKDIR /python_server

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt
RUN rm requirements.txt

COPY simple_client.py .
COPY server.py .
