#!/bin/bash
# Файл для оптимизации работы Docker файла
# Что бы каждый раз в ручную не делать миграции,
# подтягивать статику и подгружать список рецептов
python manage.py migrate --noinput && \
python manage.py collectstatic --no-input && \
python manage.py data_loading && \
gunicorn foodgram.wsgi:application --bind 0:8000