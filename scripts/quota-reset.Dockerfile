FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir "psycopg[binary]==3.2.6"

COPY scripts/reset_monthly_quota.py /app/scripts/reset_monthly_quota.py

CMD ["python3", "/app/scripts/reset_monthly_quota.py"]
