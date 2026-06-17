FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /app/static/fonts /app/static/video

COPY requirements.txt .
RUN pip install --no-cache-dir flask requests

COPY server.py correct_answers.json ./
COPY static/ static/
COPY templates/ templates/

RUN touch /app/ielts.db && chmod 666 /app/ielts.db

EXPOSE 5000

CMD ["python", "server.py"]
