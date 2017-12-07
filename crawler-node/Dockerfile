FROM python:3.6
# FROM pypy:3
ENV PYTHONUNBUFFERED 1

WORKDIR /src

ADD src/requirements.txt /requirements.txt
# RUN pip install --upgrade pip wheel
RUN pip install -r /requirements.txt
