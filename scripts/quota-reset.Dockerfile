FROM python:3.13-slim

WORKDIR /app

COPY scripts/reset_monthly_quota.py /app/scripts/reset_monthly_quota.py

CMD ["python3", "/app/scripts/reset_monthly_quota.py"]
