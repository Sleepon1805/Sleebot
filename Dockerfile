FROM python:3.12-slim

RUN mkdir /project

COPY ./requirements.txt /project
WORKDIR /project

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY ./ /project

WORKDIR /project

ENTRYPOINT python app.py