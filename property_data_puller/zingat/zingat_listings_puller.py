"""
Module to pull and clean property listings from the property listing site, Zingat (https://www.zingat.com).
"""
import os
import locale
import yaml
from datetime import date
import pandas as pd
from property_data_puller.property_listings_puller import PropertyListingsPuller


class ZingatListingsPuller(PropertyListingsPuller):
    """
    Pull property listings from the Polish real estate listing site, Domiporta.
    """
    def __init__(self):
        root_url = 'https://www.zingat.com'
        page_param = 'page'
        data_columns = ["Title", "Price", "Price currency", "Location", "Area m2", "Rooms", "Mortgage", "Date", "Advert number", "Description", "Latitude", "Longitude"]
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        listing_details_translations = yaml.safe_load(open(os.path.join(__location__, 'listing_details_translations.yml'), encoding='utf-8'))
        super().__init__(
            root_url=root_url,
            page_param=page_param,
            listing_details_translations=listing_details_translations,
            data_columns=data_columns + list(listing_details_translations.values()),
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
        listings_list = listings_page_soup.find("div", {"class": "section-items"})\
                                          .find("ul", {"class": "zc-viewport"})\
                                          .find_all("li", recursive=False)
        
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
        listing_info = listing_preview_soup.find("a", {"class": "zl-card-inner"})

        # Get the price
        listing_data["Price"] = listing_info.find("div", {"class": "zlc-features"})\
                                            .find("div", {"class": "feature-price"})\
                                            .find(text=True, recursive=False)\
                                            .text.strip()

        # Get the title
        listing_data["Title"] = listing_info.find("div", {"class": "zlc-title"}).text.strip()

        # Get the location
        listing_data["Location"] = listing_info.find("div", {"class": "zlc-location"}).text.strip()

        # Get extra details
        listing_details = listing_info.find("div", {"class": "zlc-tags"})\
                                      .find_all("span", recursive=False)
        listing_data["Rooms"] = listing_details[0].text.strip()
        listing_data["Area m2"] = listing_details[1].text.strip()

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
        url = listing_soup.find("a", {"class": "zl-card-inner"}, recursive=False)["href"]
            
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

        # Get the page header info
        page_header = listing_page_soup.find("div", {"class": "page-header"})
        listing_details["Title"] = page_header.find("h1", {"data-zingalite": "listing-detail-title"}).text.strip()
        listing_details["Price"] = page_header.find("div", {"class": "price-info-text"})\
                                              .find("strong", {"itemprop": "price"})\
                                              ["content"].strip()
        listing_details["Price currency"] = page_header.find("div", {"class": "price-info-text"})\
                                                       .find("strong", {"itemprop": "priceCurrency"})\
                                                       ["content"].strip()
        listing_details["Location"] = page_header.find("div", {"class": "detail-location-path"})\
                                                 .find("h2")\
                                                 .text.strip()

        # Get top information
        top_info = listing_page_soup.find("div", {"class": "detail-info"})
        property_size = top_info.find("label", {"data-zingalite": "property-size-value"})
        if property_size:
            listing_details["Area m2"] = property_size.text.strip()
        property_rooms = top_info.find("strong", {"data-zingalite": "property-room-count"})
        if property_rooms:
            listing_details["Rooms"] = property_rooms.text.strip()
        property_mortgage = top_info.find("strong", {"data-zingalite": "property-mortgage"})
        if property_mortgage:
            listing_details["Mortgage"] = property_mortgage.text.strip()
        for info in top_info.find_all("div", recursive=False):
            info_title = info.find("span").text.strip()
            if info_title=="İlan Tarihi":
                listing_details["Date"] = info.find("strong").text.strip()

        # Get listing details
        details = listing_page_soup.find("div", {"class": "detail-listing-properties"})\
                                   .find("ul", {"class": "attribute-detail-list"})\
                                   .find_all("li")
        for detail in details:
            detail_title = detail.find("strong", recursive=False).text.strip()
            if detail_title in self.listing_details_translations:
                detail_value = detail.find("span", recursive=False).text.strip()
                detail_title_trans = self.listing_details_translations[detail_title]
                listing_details[detail_title_trans] = detail_value

        # Get the description
        listing_details["Description"] = listing_page_soup.find("div", {"class": "detail-description"})\
                                                          .find("div", {"class": "detail-text-desktop"})\
                                                          .text.strip()

        # Get the latitude and longitude
        extra_info = listing_page_soup.find("div", {"id": "content"})\
                                      .find("div", {"id": "details"})
        listing_details["Latitude"] = extra_info["data-lat"]
        listing_details["Longitude"] = extra_info["data-lon"]

        return listing_details


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
        data["Price (num)"] = data["Price"].astype(float)
        data["Fees (num)"] = data["Fees"].str.replace('(aylık)', '', regex=False)\
                                         .str.strip()\
                                         .str.replace('TL', '', regex=False)\
                                         .str.replace('USD', '', regex=False)\
                                         .str.replace('GBP', '', regex=False)\
                                         .str.strip()\
                                         .astype(float)
        
        # Split the location column into the constituting parts
        data[["Location 1", "Location 2", "Location 3"]] = data["Location"].str.split(",", expand=True)
        for column in ["Location 1", "Location 2", "Location 3"]:
            data[column] = data[column].str.strip()

        # Process the area column
        for column in ['Area m2', 'Net m2', 'Gross m2']:
            data[f'{column} (num)'] = data[column].str.strip("m²")\
                                                .str.strip()\
                                                .replace('-', float('nan'))\
                                                .astype(float)

        # Split the rooms column
        data[["Rooms 1", "Rooms 2"]] = data["Rooms"].str.split("+", expand=True)
        for column in ["Rooms 1", "Rooms 2"]:
            data[column] = data[column].str.strip()\
                                       .replace('0 (Stüdyo)', 0)\
                                       .astype(float)

        # Format the date
        locale.setlocale(locale.LC_ALL, 'tr_TR.utf8')
        data['Date (fmt)'] = pd.to_datetime(data['Date'], format=f'%d %B %Y')

        # Format the latitude and longitude
        for column in ["Latitude", "Longitude"]:
            data[column] = data[column].astype(float)
            
        # Order the columns
        columns_order = ["Title", "Date", "Date (fmt)",
                         "Price", "Price (num)", "Price currency", "Fees", "Fees (num)", 
                         "Location", "Location 1", "Location 2", "Location 3", "Latitude", "Longitude",
                         "Area m2", "Area m2 (num)", "Gross m2", "Gross m2 (num)", "Net m2", "Net m2 (num)",
                         "Housing type", "Rooms", "Rooms 1", "Rooms 2",
                         "Mortgage", "Credit eligible", "Heating type", "Floor", "Floors in building", "Building age", "Furniture", "Building condition", "Deed status",
                         "Description", "Advert number",
                         "Page", "URL"]
        data = data[columns_order]
        data = data.dropna(axis="columns", how='all')

        return data
