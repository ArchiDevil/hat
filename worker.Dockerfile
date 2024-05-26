FROM python:3.11

RUN apt update && apt install -y dos2unix

COPY ./backend/wait-for-it.sh /app/wait-for-it.sh
COPY ./backend/run-worker.sh /app/run-worker.sh
RUN dos2unix /app/wait-for-it.sh /app/run-worker.sh

COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./backend/worker.py /app/worker.py
COPY ./backend/app /app/app

WORKDIR /app
EXPOSE 8000
CMD ["/bin/bash", "/app/run-worker.sh"]
