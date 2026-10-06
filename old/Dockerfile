FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY weather.py .
COPY transform_load.py .
COPY mart.py .

CMD ["python", "transform_load.py"]