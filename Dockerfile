FROM python:3.11

RUN mkdir -p /inventory

WORKDIR /inventory


COPY requirements.txt requirements.txt
    
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

