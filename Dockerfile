FROM python:3.11

# Встановлюємо ffmpeg та необхідні системні залежності
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файл залежностей
COPY requirements.txt .

# Встановлюємо Python-залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь проєкт
COPY . .

# Запуск
CMD ["python", "main.py"]