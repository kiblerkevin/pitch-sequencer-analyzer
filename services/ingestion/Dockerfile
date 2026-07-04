FROM python:3.12-slim-trixie AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

EXPOSE 8080

CMD ["functions-framework", "--target=ingest", "--port=8080", "--source=app/live.py"]
