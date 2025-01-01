FROM python:3.12-slim

RUN apt update && apt install -y dos2unix

COPY ./backend/wait-for-it.sh /app/wait-for-it.sh
COPY ./backend/run.sh /app/run.sh
RUN dos2unix /app/wait-for-it.sh /app/run.sh

COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./backend/alembic /app/alembic
COPY ./backend/alembic.ini /app/alembic.ini

COPY ./backend/manage.py /app/manage.py
COPY ./backend/main.py /app/main.py
COPY ./backend/app /app/app

WORKDIR /app
EXPOSE 8000
CMD ["/bin/bash", "/app/run.sh"]
