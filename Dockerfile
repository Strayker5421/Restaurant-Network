FROM python:3.11.4

WORKDIR /app

RUN adduser appuser

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
COPY run.py config.py boot.sh ./

RUN chmod +x boot.sh
ENV FLASK_APP run.py
RUN chown -R appuser:appuser ./

USER appuser

EXPOSE 5001
ENTRYPOINT ["./boot.sh"]