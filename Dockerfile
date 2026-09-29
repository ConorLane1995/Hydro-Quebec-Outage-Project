FROM python:3.13-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY collector.py .
COPY roadwork_collector.py .
CMD ["python", "collector.py"]

