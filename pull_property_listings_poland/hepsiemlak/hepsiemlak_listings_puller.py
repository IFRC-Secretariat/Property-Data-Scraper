"""
Module to pull and clean property listings from the property listing site, Hepsiemlak (https://www.hepsiemlak.com).

Categories of properties supported are:
- Apartments
- Houses
- Rooms
"""
import os
import yaml
import pandas as pd
from pull_property_listings_poland.property_listings_puller import PropertyListingsPuller


class HepsiemlakListingsPuller(PropertyListingsPuller):
    """
    Pull property listings from the Polish real estate listing site, Domiporta.
    """
    def __init__(self):
        root_url = 'https://www.hepsiemlak.com'
        page_param = 'page'
        listing_categories = {'rental': 'kiralik'}
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        listing_details_translations = yaml.safe_load(open(os.path.join(__location__, 'listing_details_translations.yml'), encoding='utf-8'))
        super().__init__(root_url=root_url,
                         page_param=page_param,
                         listing_categories=listing_categories,
                         listing_details_translations=listing_details_translations)


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
        listings_list = listings_page_soup.find("ul", {"class": "list-items-container"})\
                                          .find_all("li", {"class": "listing-item"})

        return listings_list


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
        url = listing_soup.find("div", {"class": "list-view-content"})\
                        .find("div", {"class": "links"})\
                        .find("a")["href"]
            
        return url


    def get_listing_details(self, listing_page_soup):
        """
        Get details of the property listing from the listing soup.

        Parameters
        ----------
        listing_page_soup : BeautifulSoup (required)
            Soup of the listing page.

        Returns
        -------
        listing_details : dict
            Dictionary mapping listing detail names to content, e.g. {"title": "My listing", "category": "flat"}.
        """
        # Store all data in a dict
        listing_details = {}
        listing_soup_details = listing_page_soup.find("section", {"class": "det-block"})

        # Get the listing title and price
        listing_upper_details = listing_soup_details.find("div", {"class": "det-title-upper"})
        listing_details["Title"] = listing_upper_details.find("div", {"class": "left"})\
                                                        .find("h1")\
                                                        .text.strip()
        listing_details["Price"] = listing_upper_details.find("div", {"class": "right"})\
                                                        .find("p", {"class": "price"})\
                                                        .text.strip()

        # Get the listing info summarised
        listing_summary = listing_soup_details.find("div", {"class": "det-title-bottom"})\
                                              .find("ul", {"class": "short-info-list"})\
                                              .find_all("li")
        if len(listing_summary)==7:
            listing_details["Location 1"] = listing_summary[0].text.strip()
            listing_details["Location 2"] = listing_summary[1].text.strip()
            listing_details["Location 3"] = listing_summary[2].text.strip()
            listing_details["Listing category"] = listing_summary[3].text.strip()
            listing_details["Total m2"] = listing_summary[6].text.replace('m2', '').strip()
            

        # Get the listing details by looping through the items in the list
        listing_block_details = listing_soup_details.find("div", {"class": "det-adv-info"})
        for details_list in listing_block_details.find_all("ul"):
            for detail in details_list.find_all("li"):
                detail_title = detail.find("span", {"class": "txt"}).text.strip()
                if detail_title in self.listing_details_translations:
                    detail_value = detail.find_all()[1].text.strip() if len(detail.find_all())>1 else None
                    detail_title_trans = self.listing_details_translations[detail_title]
                    listing_details[detail_title_trans] = detail_value

        # Get the ad description
        listing_description_section = listing_page_soup.find("section", {"class": "description"})
        listing_details["Description"] = listing_description_section.find("section", {"class": "det-block"})\
                                                                    .find("div", {"class": "description-content"})\
                                                                    .find("div", {"class": "description"})\
                                                                    .text.strip()

        return listing_details


    def process_listing_data(self, data):
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
        data['Price (num)'] = data['Price'].str.replace('TL', '', regex=False)\
                                         .str.replace('.','', regex=False)\
                                         .str.strip()\
                                         .astype(float, errors='ignore')
        data['Deposit (num)'] = data['Deposit'].str.replace('TL', '', regex=False)\
                                               .str.replace('.','', regex=False)\
                                               .str.strip()\
                                               .astype(float, errors='ignore')
        
        # Convert dates
        data['Update date'] = pd.to_datetime(data['Update date'], errors='ignore', format='yyyy-mm-dd')

        # Convert number of rooms and square metres to number
        data['Rooms'] = data['Rooms + halls'].str.split('+').str[0]\
                                                .str.strip()\
                                                .astype(float, errors='ignore')
        data['Halls'] = data['Rooms + halls'].str.split('+').str[1]\
                                                .str.strip()\
                                                .astype(float, errors='ignore')

        # Order the columns
        first_columns = ['Title', 'Update date',
                         'Price', 'Price (num)', 
                         'Location 1', 'Location 2', 'Location 3', 
                         'Listing category', 'Property type', 
                         'Rooms', 'Halls', 'Total m2',
                         'Deposit (num)']
        last_columns = ['page', 'url']
        columns_order = first_columns+[column for column in data.columns if column not in first_columns+last_columns]+last_columns
        data = data[columns_order]

        return data
