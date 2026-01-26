FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 5200

CMD ["gunicorn", "-k", "gthread", "-w", "1", "--threads", "1", "-t", "120", "-b", "0.0.0.0:5200", "wsgi:app"]
