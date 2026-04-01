FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

COPY bot/requirements.txt bot/requirements.txt
RUN pip install --no-cache-dir -r bot/requirements.txt

CMD ["python", "-m", "bot.main"]
