FROM python:3.9-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Порт 10000 открываем для Render
EXPOSE 10000
CMD ["python", "bot.py"]
