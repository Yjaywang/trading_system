import requests
from bs4 import BeautifulSoup


def post_form_data(url, form_data):
    try:
        response = requests.post(url, data=form_data)
        if 'application/json' in response.headers.get('Content-Type', ''):
            return response.json()
        else:
            return response
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return {}


def parse_html(response):
    if 'text/html' in response.headers.get('Content-Type', ''):
        soup = BeautifulSoup(response.text, 'html.parser')
        tbody = soup.find('tbody')
        if tbody and not isinstance(tbody, str):
            rows = tbody.find_all('tr')
            table_data = []
            for row in rows:
                # Extract text from each td in the row
                cols = [td.get_text(strip=True) for td in row.find_all('td')]
                table_data.append(cols)
            return table_data
        else:
            return "No tbody found in the HTML."
    else:
        return "The response is not HTML."
