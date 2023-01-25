FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN mkdir logs
COPY . .
COPY .env .

CMD ["python3", "chatgpt-signal-bot.py"]

