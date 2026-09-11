FROM python:3.12-slim
RUN pip install --no-cache-dir fastapi==0.115.0 uvicorn==0.30.6
WORKDIR /app
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
