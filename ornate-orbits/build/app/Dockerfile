FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip setuptools

RUN mkdir app
WORKDIR /app

COPY ./app/ ./app/
COPY ./trivia.db ./trivia.db
COPY ./requirements-dev.txt .

RUN pip install watchdog==4.0.1
RUN pip install -r requirements-dev.txt

CMD ["bash", "./app/entrypoint.sh"]
