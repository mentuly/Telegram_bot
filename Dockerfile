FROM python:3.13-slim

# Встановлюємо ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Створення робочої директорії
WORKDIR /app

# Копіюємо залежності
COPY requirements.txt .

# Встановлюємо залежності Python
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код бота
COPY . .

# Запускаємо бота
CMD ["python", "main.py"]