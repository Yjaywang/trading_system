FROM python:3.10

WORKDIR /trading_system

COPY requirements.txt .

ENV PYTHONUNBUFFERED=1

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]