FROM python:3.13-slim

WORKDIR /app

# Установка Poetry и других зависимостей
RUN pip install poetry==1.8.2 && \
    apt-get update && \
    apt-get install -y netcat-openbsd && \
    pip install bcrypt  

# Копирование файлов конфигурации Poetry
COPY pyproject.toml poetry.lock* ./

# Установка зависимостей
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi && \
    pip install pydantic-settings bcrypt  # Устанавливаем pydantic-settings и bcrypt

# Копирование кода приложения
COPY . .

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]