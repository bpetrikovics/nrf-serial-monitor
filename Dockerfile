FROM python:3.9-slim

LABEL Maintainer="bpetrikovics@gmail.com"

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY serialmonitor.py ./

ENTRYPOINT ["./serialmonitor.py"]
