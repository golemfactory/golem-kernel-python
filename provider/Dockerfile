FROM maugnorbert/docker_golem_cuda_base

WORKDIR /usr/src/app
VOLUME /usr/src/app/workdir /usr/src/app/tmp
#RUN chmod 777 /usr/src/app/workdir /usr/src/app/tmp

RUN apt-get update && apt-get install -y python3-pip python3.8-venv pciutils curl net-tools

COPY requirements.txt .
RUN python3 -m venv /usr/src/app/venv

RUN /usr/src/app/venv/bin/pip install wheel setuptools
RUN /usr/src/app/venv/bin/pip install -r requirements.txt
RUN rm requirements.txt

COPY server.py .
COPY wait_for_server.sh .
COPY wait_for_kernel.sh .
COPY simple_client.py .
COPY gdrive.py .
COPY settings.yaml .

# Temp dir some storage
# Disabling Pip progress bar so that long-lasting installations do not send too much data to stdout
ENV TMPDIR=/usr/src/app/tmp PIP_PROGRESS_BAR=off
