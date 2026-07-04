FROM python:3.12-slim-trixie AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/packages -r requirements.txt

FROM gcr.io/distroless/python3-debian12

WORKDIR /app
COPY --from=builder /app/packages /app/packages
COPY app/ app/

ENV PYTHONPATH=/app/packages

EXPOSE 8080

CMD ["python3", "-m", "gunicorn", "--bind", "0.0.0.0:8080", "app.main:app"]
