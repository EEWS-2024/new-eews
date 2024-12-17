FROM python:3.11

WORKDIR /app
COPY . /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "main.py"]
