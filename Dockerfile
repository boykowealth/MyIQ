FROM python:3.10

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libmagic-dev \
    && pip install --no-cache-dir -r requirements.txt

CMD ["python", "app/main.py"]
