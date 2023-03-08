"""
Module to pull and clean property listings from the property listing site, Emlakjet (https://www.emlakjet.com/).
"""
import os
import locale
import yaml
from datetime import date
import pandas as pd
from property_data_scraper.property_listings_puller import PropertyListingsPuller


class EmlakjetListingsPuller(PropertyListingsPuller):
    """
    Pull property listings from the Polish real estate listing site, Domiporta.
    """
    def __init__(self):
        root_url = 'https://www.emlakjet.com'
        page_param = 'page'
        data_columns = ["Title", "Price", "Price (unit)", "Rooms", "Property type", "Floor", "Area m2", "Date", "Location"]
        super().__init__(
            root_url=root_url,
            page_param=None,
            page_in_url=True,
            listing_details_translations=None,
            data_columns=data_columns,
        )


    def get_listings_list(self, listings_page_soup):
        """
        Get the list of listings from the listings page.

        Parameters
        ----------
        listings_page_soup : BeautifulSoup (required)
            Soup of the listings page.

        Returns
        -------
        listings_list : list
            List of listings.
        """
        listings_list = listings_page_soup.find("div", {"id": "listing-search-wrapper"})\
                                          .find_all("div", {"class": "_3qUI9q"}, recursive=False)

        return listings_list


    def get_listing_preview_data(self, listing_preview_soup):
        """
        Get information from the listing on the listings page.

        Parameters
        ----------
        listing_preview_soup : BeautifulSoup (required)
            Soup of the single listing on the listings page.

        Returns
        -------
        listing_data : dict
            Dictionary mapping listing detail names to content, e.g. {"title": "My listing", "category": "flat"}.
        """
        listing_data = {}
        listing_info = listing_preview_soup.find("a", {"class": "_3qUI9q"})\
                                           .find("div", {"class": "manJWF"})

        # Get the title
        listing_data["Title"] = listing_info.find("div", {"class": "_1TNSG2"}).text.strip()

        # Get the details
        listing_details = listing_info.find("div", {"class": "_2UELHn"})\
                                      .find_all("span", recursive=False)
        detail_names = {"home": "Property type", "weekend": "Rooms", "layers": "Floor", "texture": "Area m2"}
        for detail in listing_details:
            detail_id = detail.find("i", {"class": "material-icons"}).text.strip()
            if detail_id in detail_names:
                listing_data[detail_names[detail_id]] = detail.find(text=True, recursive=False).strip()
            elif detail_id=="event":
                listing_data["Date"] = detail.find("span").text.strip()

        # Get the price
        price_details = listing_info.find("div", {"class": "_3Q-7xT"})\
                                    .find("p", {"class": "_2C5UCT"})\
                                    .find("span", recursive=False)\
                                    .find_all(text=True)
        listing_data["Price"] = price_details[0].text.replace('.','').replace(',','').strip()
        listing_data["Price (unit)"] = price_details[1].text.strip()

        # Get the location info
        listing_data["Location"] = listing_info.find("div", {"class": "_2wVG12"}).text.strip()

        return listing_data


    def get_listing_url(self, listing_soup):
        """
        Get the relative url of a single listing from the single listing soup on the listings page.

        Parameters
        ----------
        listing_soup : BeautifulSoup (required)
            Soup of the listing from the listings list.

        Returns
        -------
        url : string
            Relative URL of the single listing.
        """
        url = listing_soup.find("a", {"class": "_3qUI9q"}, recursive=False)["href"]
            
        return url


    def process_data(self, data):
        """
        Process the dataset of listings, including removing units from columns and converting to numbers, and ordering the columns.

        Parameters
        ----------
        data : Pandas DataFrame (required)
            Pandas DataFrame with one row per listing.

        Returns
        -------
        data : Pandas DataFrame
            Pandas DataFrame of processed data.
        """
        # Convert the price data to numeric
        data['Price (num)'] = data['Price'].astype(str)\
                                           .str.replace(".", "", regex=False)\
                                           .str.strip()\
                                           .astype(float, errors='ignore')

        # Convert dates
        locale.setlocale(locale.LC_ALL, 'tr_TR.utf8')
        data['Date'] = data['Date']+f' {date.today().year}'
        data['Date (fmt)'] = pd.to_datetime(data['Date'], format=f'%d %B %Y')

        # Split the location into the three options
        data[['Location 1', 'Location 2', 'Location 3']] = data['Location'].str.split(' - ', expand=True)

        # Convert square metres to number
        data['Area m2 (num)'] = data['Area m2'].str.strip()\
                                               .str.strip('m2')\
                                               .str.strip()\
                                               .replace('', None)\
                                               .astype(float)

        # Convert number of rooms to number
        data[['Rooms 1', 'Rooms 2']] = data['Rooms'].str.split('+', expand=True)
        for room_name in ['Rooms 1', 'Rooms 2']:
            data[room_name] = data[room_name].str.strip('Oda')\
                                             .str.strip()\
                                             .replace('', None)\
                                             .replace('Stüdyo', None)\
                                             .astype(float)

        # Order the columns
        first_columns = ["Title", "Date", "Date (fmt)", 
                         "Price", "Price (num)", "Price (unit)", 
                         "Location", "Location 1", "Location 2", "Location 3",
                         "Area m2", "Area m2 (num)",
                         "Property type", "Rooms", "Rooms 1", "Rooms 2", "Floor"]
        last_columns = ['Page', 'URL']
        data = data[first_columns+last_columns]
        data = data.dropna(axis="columns", how='all')

        return data
