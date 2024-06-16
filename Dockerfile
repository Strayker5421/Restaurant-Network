FROM python:3.11.4-slim-buster

WORKDIR /app

RUN adduser appuser

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y docker.io
RUN apt-get install -y postgresql-client
RUN chmod +x /usr/bin/docker
RUN apt-get install -y curl
RUN curl -L "https://github.com/docker/compose/releases/download/v2.27.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
RUN chmod +x /usr/local/bin/docker-compose

ENV TZ=Europe/Moscow
RUN apt-get update && apt-get install -y tzdata

COPY app app
COPY run.py docker-compose-menu.yml docker-compose-nginx.yml config.py boot.sh bootmenu.sh nginx.conf ./

RUN chmod +x boot.sh
RUN chmod +x bootmenu.sh
ENV FLASK_APP run.py
RUN chown -R appuser:appuser ./

USER root

EXPOSE 80
ENTRYPOINT ["./boot.sh"]