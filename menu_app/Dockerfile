FROM python:3.11.4-slim-buster

WORKDIR /app

RUN adduser appuser

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN pip install --no-cache-dir -r requirements.txt

COPY ./menu_app/app app
COPY ./menu_app/run.py ./run.py
COPY ./menu_app/config.py ./config.py
COPY ./menu_app/bootmenu.sh ./bootmenu.sh


RUN chmod +x bootmenu.sh
ENV FLASK_APP run.py
RUN chown -R appuser:appuser ./

USER appuser

EXPOSE 80
ENTRYPOINT ["./bootmenu.sh"]