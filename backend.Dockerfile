FROM python:3.11-alpine

COPY ./backend/app /app/app
COPY ./backend/requirements.txt /app/requirements.txt

WORKDIR /app
RUN pip install -r ./requirements.txt

CMD ["hypercorn", "-b", "0.0.0.0:8000", "--workers=4", "--access-logfile", "-", "--error-logfile", "-"]
