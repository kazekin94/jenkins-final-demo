FROM python:3.7-slim

RUN apt-get update -y

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt 

EXPOSE 8000

RUN python manage.py migrate 

CMD python manage.py runserver 0.0.0.0:8000 