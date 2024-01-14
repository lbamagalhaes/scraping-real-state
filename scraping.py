import requests
import re
from bs4 import BeautifulSoup
import pandas as pd


def process_main_name(main_name):
    # Splitting the main name into address, neighborhood, and city
    parts = main_name.replace('                                   ', ',').split(',')
    address = parts[0].strip()
    neighborhood = parts[1].strip()
    city = parts[2].strip()
    return address, neighborhood, city

def process_price(price_str):
    # Splitting the price string into price and price per square meter
    if 'Sob Consulta' in price_str:
        return None, None
    elif 'Valor m²'in price_str:
        parts = price_str.split('Valor m² ')
        price = int(parts[0].strip().replace('R$ ', '').strip().replace('.', ''))
        price_per_sqm = int(parts[1].strip().replace('R$ ', '').strip().replace('.', '') if len(parts) > 1 else None)
    elif 'A partir de'in price_str:
        parts = price_str.split('A partir de ')
        price = int(parts[1].strip().replace('R$ ', '').strip().replace('.', ''))
        price_per_sqm = None
    else:
        price = int(price_str.replace('R$ ', '').strip().replace('.', ''))
        price_per_sqm = None

    return price, price_per_sqm

def scrape_apartment_data(apartment):
    try:
        # Extract the main name and process it
        main_name = apartment.find('h2', {'class': 'new-title phrase'}).text.strip()
        address, neighborhood, city = process_main_name(main_name)

        # Extract price and process it
        price_info = apartment.find('div', {'class': 'new-price'}).text.strip()
        price, price_per_sqm = process_price(price_info)

        # Extracting details from <ul class="new-details-ul">
        details_list = apartment.find('ul', {'class': 'new-details-ul'})
        details = [li.text.strip() for li in details_list.find_all('li')]       
        
        # Parsing details to get rooms, suites, and parking lots
        rooms, suites, parking_lots = None, None, None
        for detail in details:
            if 'quarto' in detail.lower():
                rooms = int(detail.lower().replace(' quartos', ''))
            elif 'suíte' in detail.lower():
                suites = int(detail.lower().replace(' suítes', ''))
            elif 'vaga' in detail.lower():
                parking_lots = int(detail.lower().replace(' vagas', ''))

        return {
            'Endereco': address,
            'Bairro': neighborhood,
            'Cidade': city,
            'Preco': price,
            'Preco por m2': price_per_sqm,
            'Quartos': rooms,
            'Suites': suites,
            'Vagas': parking_lots
        }
    except Exception as e:
        print(f'Error extracting apartment data: {e}')
        return None

# Base URL of the website
base_url = 'https://www.dfimoveis.com.br'

# DataFrame to store the extracted data
apartments_df = pd.DataFrame()

# Loop through all 18 pages
for page in range(1, 19):
    print(f'Extracting page {page}...')
    url = f'{base_url}/venda/df/brasilia/apartamento?quartosinicial=2&quartosfinal=3&suitesinicial=2&suitesfinal=3&page={page}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all apartment links in the page
    apartment_links = soup.find_all('a', {'class': 'new-card'})

    # Extract data for each apartment and add it to the DataFrame
    for link in apartment_links:
        apt_data = scrape_apartment_data(link)
        if apt_data:
            apartments_df = apartments_df.append(apt_data, ignore_index=True)

apartments_df.to_excel('apartments.xlsx', index=False)
