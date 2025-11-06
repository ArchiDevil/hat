FROM python:3.12-slim

COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

RUN python3 -m nltk.downloader punkt_tab

COPY ./backend/worker.py /app/worker.py
COPY ./backend/app /app/app

WORKDIR /app
EXPOSE 8000
CMD ["python3", "/app/worker.py"]
