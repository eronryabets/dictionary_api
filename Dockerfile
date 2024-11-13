
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Скопируем все файлы проекта в контейнер
COPY . /app/

# Открываем порт 8000 для доступа к приложению из контейнера.
EXPOSE 8000

# Выполнение миграций
#RUN python manage.py makemigrations && python manage.py migrate

# Запуск тестов
# RUN python manage.py test

# Команда для запуска Gunicorn
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "dictionary_api.wsgi:application"]