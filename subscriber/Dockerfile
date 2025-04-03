FROM python:3.10

WORKDIR /app
COPY main.py .

RUN pip install paho-mqtt pymongo

CMD ["python", "main.py"]
