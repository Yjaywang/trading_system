# trading_system
Crawl futures and options data, analyze the data, generate trading signals, and execute trades. That's it.

python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

django-admin startproject trading_system
cd trading_system
django-admin startapp core
python manage.py makemigrations
python manage.py migrate
python manage.py runserver