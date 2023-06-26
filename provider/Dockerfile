#FROM ubuntu:focal-20220801
FROM python:3.10-alpine

WORKDIR /usr/src/app
VOLUME /usr/src/app/workdir /usr/src/app/tmp

#RUN apt-get update && apt-get install -y python3-pip python3.8-venv pciutils curl net-tools
RUN apk add --no-cache g++ python3-dev py3-pip

COPY requirements.txt .
RUN python3 -m venv /usr/src/app/venv

RUN /usr/src/app/venv/bin/pip install wheel setuptools

#RUN echo $(python -c "import sys; print(sys.version)")
#RUN echo $(python -c "import struct; print(struct.calcsize('P')*8)")

RUN /usr/src/app/venv/bin/pip install -r requirements.txt
RUN pip install --upgrade https://storage.googleapis.com/tensorflow/linux/cpu/tensorflow_cpu-2.12.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
RUN rm requirements.txt

COPY pip.conf /usr/src/app/venv/
COPY server.py .
COPY wait_for_server.sh .
COPY wait_for_kernel.sh .
COPY simple_client.py .
COPY gdrive.py .
COPY settings.yaml .

# Temp dir some storage
# Disabling Pip progress bar so that long-lasting installations do not send too much data to stdout
ENV TMPDIR=/usr/src/app/tmp PIP_PROGRESS_BAR=off
