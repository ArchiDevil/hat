FROM python:3.11-alpine

COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./backend/asgi.py /app/asgi.py
COPY ./backend/app /app/app

WORKDIR /app
EXPOSE 8000
CMD ["hypercorn", "-b", "0.0.0.0:8000", "--workers=4", "--access-logfile", "-", "--error-logfile", "-", "asgi:app"]
