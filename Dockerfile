FROM ubuntu:18.04

USER root

WORKDIR /app

COPY . .

RUN apt-get update -y && apt-get install -y python3 python3-pip wget dos2unix sudo lsb-release iproute2

RUN dos2unix provision.sh && dos2unix requirement.txt

RUN chmod +x ./provision.sh && ./provision.sh

RUN echo 'export PATH="/home/root/.local/bin:$PATH"' >> ~/.bashrc

RUN python3 -m pip install requests

RUN python3 -m pip install -r ./requirement.txt

RUN service mysql start && ./provision.sh && python manage.py makemigrations && python manage.py migrate

CMD bash

CMD service mysql start && python ./manage.py runserver 0.0.0.0:8000

EXPOSE 8000

