FROM python:3.9-slim
# Устанавливаем Java (нужна для подписи APK)
RUN apt-get update && apt-get install -y default-jdk apksigndebuger || apt-get install -y openjdk-17-jre-headless
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Скачиваем простенький подписыватель (утилиту)
RUN apt-get install -y zip
EXPOSE 10000
CMD ["python", "bot.py"]
