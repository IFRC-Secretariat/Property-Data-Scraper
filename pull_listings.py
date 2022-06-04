"""
Script to pull rental listings for the Polish estate agent website, Domiporta (https://www.domiporta.pl/).

Note that data will be appended to the file in the data folder, so this file should be deleted if you want to create a new file.
"""
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import yaml
from collections import Counter

"""
SETUP
- Read in the file detailing the translations of listing details
- Set variables including the root URL and location for writing the results
"""
# Read in listing information
listing_detail_translations = yaml.safe_load(open('listing_details.yml'))
unrecognised_details = []
root_url = 'https://www.domiporta.pl'
data_write_path = 'data/domiporta_rental_listings.csv'

# Warn the user if the data will append
if os.path.exists(data_write_path):
    input(f'WARNING: data will append to the existing data file at {data_write_path}. Press enter to continue.')


"""
LOOP THROUGH LISTING PAGES
- Loop through and request each page of listings, and convert to soup
- Extract the list of individual listings
- Get the URL for each listing
- Request the listing URL and convert to soup
"""
# Loop through the listing pages
page_number = 196
while True:
    print(f'\nSearching listings in page {page_number}...')
    data = pd.DataFrame()
    listings_page = requests.get(f'{root_url}/nieruchomosci/wynajme?PageNumber={page_number}')
    listings_soup = BeautifulSoup(listings_page.content, "html.parser")

    # Get the listings and loop through
    listings = listings_soup.find("div", {"class": "listing"}).find("div", {"class": "listing__container"}).find("ul", {"class": "grid"}).find_all("li", {"class": "grid-item"})
    if not listings: break
    for single_listing in listings:

        # Get the url for the individual listing
        sneakpeek_info = single_listing.find("div", {"class": "sneakpeak__data"})
        if not sneakpeek_info: continue
        single_listing_url = sneakpeek_info.find("a", {"class": "sneakpeak__title"})['href']
        single_page = requests.get(f'{root_url}{single_listing_url}')
        single_soup = BeautifulSoup(single_page.content, "html.parser")


        """
        EXTRACT INDIVIDUAL LISTING INFORMATION
        - Get the header information including title and price
        - Get all information in the details and extract the values in the right way
        - Append all data to a dataframe
        """
        # Extract information from the header
        try:
            single_listing_info = {}
            header_section = single_soup.find("div", {"class": "detials__header-section"})
            single_listing_info["title"] = header_section.find("span", {"class": "summary__subtitle-2"}).text.strip()

            # Get the price and currency
            price_info = header_section.find("span", {"class": "summary__price_number"})
            price_number = price_info.find("span", {"itemprop": "price"})
            if price_number:
                single_listing_info["price"] = price_number["content"]
                single_listing_info["currency"] = price_info.find("span", {"itemprop": "priceCurrency"})["content"]
            else:
                single_listing_info["price"] = price_info.text.strip()

            # Extract information from the details section
            details_section = single_soup.find("section", {"class": ["detials__section", "features"]}).find("div", {"class": "features__container"}).find("ul", {"class": "features__list-2"}).find_all("li")
            for item in details_section:
                detail_title = item.find("span", {"class": "features__item_name"})
                if not detail_title: continue
                detail_title = detail_title.text.strip()
                detail_value = item.find("span", {"class": "features__item_value"})

                # Check if the information is known
                if detail_title not in listing_detail_translations:
                    unrecognised_details.append(detail_title.strip())
                    continue

                # Extract the information depending on which item
                detail_title_trans = listing_detail_translations[detail_title]
                if detail_title=='Lokalizacja':
                    address_details = detail_value.find("span", {"itemprop": "address"})
                    single_listing_info["address_locality"] = address_details.find("span", {"itemprop": "addressLocality"}).text.strip()
                    street_address = address_details.find("span", {"itemprop": "streetAddress"})
                    if street_address:
                        single_listing_info["street_address"] = street_address.text.strip()
                    region_info = address_details.find("meta", {"itemprop": "addressRegion"})
                    if region_info:
                        single_listing_info["region"] = region_info["content"].strip()
                    country_info = address_details.find("meta", {"itemprop": "addressCountry"})
                    if country_info:
                        single_listing_info["country"] = country_info["content"].strip()
                    geo = detail_value.find("span", {"itemprop": "geo"})
                    if geo:
                        single_listing_info["latitude"] = geo.find("meta", {"itemprop": "latitude"})["content"].strip()
                        single_listing_info["longitude"] = geo.find("meta", {"itemprop": "longitude"})["content"].strip()
                elif detail_title in ['Kategoria', 'Przeznaczenie']:
                    single_listing_info[detail_title_trans] = detail_value.find("a").text.strip()
                else:
                    single_listing_info[detail_title_trans] = detail_value.text.strip()

            single_listing_info['url'] = root_url+single_listing_url

        except Exception as err:
            print(f'Error with listing {root_url}{single_listing_url}')
            raise RuntimeError(err)

        # Append the data to the dataframe
        data = data.append(single_listing_info, ignore_index=True)


    """
    PROCESS AND SAVE THE DATA
    - Process the data including converting strings to number types, e.g. for price and surface area
    - Order the columns so that the result is the same each time
    - Append the data to the existing data file
    """
    # Print some information
    if unrecognised_details:
        print(f'Unrecognised details: {Counter(unrecognised_details)}')

    # Process the data to convert numbers with units to just numbers
    def convert_units_to_num(price, unit=None):
        try:
            price_num = float(''.join(price.strip().split(unit)[0].replace(',','.').split()))
            return price_num
        except:
            return
    data['price_num'] = data['price'].apply(lambda x: convert_units_to_num(x, unit='zł'))
    data['price_zl_per_m2_num'] = data['price_zl_per_m2'].apply(lambda x: convert_units_to_num(x, unit='zł/m'))
    data['surface_area_m2_num'] = data['surface_area_m2'].apply(lambda x: convert_units_to_num(x, unit='m2'))
    data['latitude'] = data['latitude'].apply(lambda x: convert_units_to_num(x))
    data['longitude'] = data['longitude'].apply(lambda x: convert_units_to_num(x))

    # Order the columns so that the appending to the data is consistent
    columns_order = ['title', 'price', 'price_num', 'currency', 'price_zl_per_m2', 'price_zl_per_m2_num', 'surface_area_m2', 'surface_area_m2_num', 'address_locality', 'street_address', 'region', 'country', 'latitude', 'longitude']
    columns_order += [item for item in list(listing_detail_translations.values()) if item not in columns_order] + ['url']
    for column in columns_order:
        if column not in data.columns:
            data[column] = ''
    missed_columns = [column for column in data.columns if column not in columns_order]
    if missed_columns:
        raise RuntimeError(f'Missing columns: {missed_columns}')
    data = data[columns_order]

    # Save: append to the existing data file
    print('Saving data...')
    data.to_csv(data_write_path, index=False, header=not os.path.exists(data_write_path), mode='a')
    page_number += 1
