"""
Module for pulling rental listings from property listing sites.

Note that this is a generic base class and shouldn't be used by itself, only through its derived classes.
"""
import os
import traceback
from urllib.parse import urlparse
import pandas as pd
import requests
from bs4 import BeautifulSoup


class PropertyListingsPuller:
    """
    Class to pull listings from property listing websites and return a dataset.

    Parameters
    ----------
    root_url : string (required)
        The root url of the website.

    page_param : string (required)
        The name of the parameter that is in the URL to specify the page number.

    data_columns : list (required)
        List of the columns/ information from the listings, e.g. ['Title', 'Price', 'Description'].
        This is required because the data for each listing page is appended to the CSV file, so this ensures that the columns are the same each time.

    listing_details_translations : dict (default=None)
        Dictionary mapping listing detail names to a translation. The order of keys will also be used to order the columns of the final dataset. 
    """
    def __init__(self, root_url, page_param, data_columns, listing_details_translations=None):
        self.root_url = root_url
        self.page_param = page_param
        self.data_columns = data_columns
        if listing_details_translations is None:
            listing_details_translations = []
        self.listing_details_translations = listing_details_translations


    def pull_listings(self, data_write_path, listing_page_slug, get_listing_previews=True, get_listing_pages=True, page_start=1, page_end=None):
        """
        Pull a dataset of listings from the property website and save it to a file.
        By default results are appended to the file to enable stopping and starting.

        Parameters
        ----------
        data_write_path : string (required)
            The location of the CSV file to write the dataset of listings to.
            Note that this is required so that the data is saved after every page, because often there are a lot of pages, so if the program crashes before finishing all the pages there is still data saved.

        listing_page_slug : string (required)
            A slug to be added to the root url to give the URL of the listings page.

        get_listing_previews : bool (default=True)
            If True, information will be extracted from the listing preview (the listing details on the listings page).

        get_listing_pages : bool (default=True)
            If True, each single listing page will be requested and information will be extracted.

        page_start : int (default=1)
            Number of the page to start, starting from 1.

        page_end : int (default=None)
            Number of pages to pull. If None, all pages will be pulled.
        """
        # Loop through listing pages and pull data
        page_number = page_start
        while True:
            data = []
            listings_page_url = f'{self.root_url}/{listing_page_slug}?{self.page_param}={page_number}'
            print(f'\nSearching listings in page {page_number}... {listings_page_url}')
            try:
                listings_page = requests.get(listings_page_url)
            except requests.exceptions.ChunkedEncodingError as err:
                break
            listings_soup = BeautifulSoup(listings_page.content, "html.parser")

            # Get the listings and check if redirect or empty page
            try:
                listings = self.get_listings_list(listings_soup)
            except AttributeError as err:
                break
            if not listings:
                break
            if listings_page.history and page_number!=1:
                if listings_page.history[0].status_code in [301, 302]:
                    break

            # Loop through all listings on the page
            for i, single_listing in enumerate(listings):
                listing_data = {}

                # Get the information from the listing preview on the listings page
                if get_listing_previews:
                    try:
                        listing_preview_info = self.get_listing_preview_data(single_listing)
                        listing_data = {**listing_data, **listing_preview_info}
                    except NotImplementedError as err:
                        continue

                # Get the single listing URL
                listing_data['Page'] = page_number
                try:
                    single_listing_url = self.get_listing_url(single_listing)
                    single_listing_url = self.convert_relative_url(single_listing_url)
                    listing_data["URL"] = single_listing_url
                except Exception as err:
                    print(f'Error with finding the URL for listing {i} on page {listings_page_url}')

                # Request the single listing page and extract the listing information
                if get_listing_pages and single_listing_url:
                    print(single_listing_url)
                    max_attempts = 20
                    for attempt in range(1, max_attempts+1):
                        try:
                            single_page = requests.get(f'{single_listing_url}')
                            single_soup = BeautifulSoup(single_page.content, "html.parser")
                            single_listing_info = self.get_listing_details(listing_page_soup=single_soup)
                            break
                        except Exception as err:
                            error_message = f'\nSkipping listing due to error: {single_listing_url}\n{str(err)}'
                            f = open("log.txt", "a")
                            f.write(error_message)
                            f.close()
                            print(err)
                            print(traceback.format_exc())
                    listing_data = {**listing_data, **single_listing_info}

                # Append the listing data to the main data
                data.append(listing_data)

            # Save the dataset: write with header if it is the first time, else append
            print('Saving data...')
            if page_number==page_start:
                header = True; mode = 'w'
            else:
                header = False; mode = 'a'
            data = pd.DataFrame(data)
            data = data.reindex(columns=self.data_columns+["Page", "URL"])
            data.to_csv(data_write_path, index=False, header=header, mode=mode)

            # Increment the pages or end if on the end page
            if page_end is not None:
                if page_number >= page_end:
                    break
            page_number += 1


    def get_listings_list(self, listings_page_soup):
        """
        Get the list of listings from the listings page. This method should be defined in the child class so raise a NotImplementedError.

        Parameters
        ----------
        listings_page_soup : BeautifulSoup (required)
            Soup of the listings page.

        Returns
        -------
        listings_list : list
            List of listings.
        """
        raise NotImplementedError


    def get_listing_preview_data(self, listing_preview_soup):
        """
        Get the list of listings from the listings page. This method should be defined in the child class so raise a NotImplementedError.

        Parameters
        ----------
        listing_preview_soup : BeautifulSoup (required)
            Soup of the listing preview (element of the listings list).
        """
        raise NotImplementedError


    def convert_relative_url(self, url):
        """
        Convert a relative URL to an absolute URL.
        If the URL is an absolute URL of another site, raise an error.

        Parameters
        ----------
        url : string (required)
            URL to be checked.
        """
        if not url:
            return

        # Check if the URL is relative or absolute
        url_hostname = urlparse(url).hostname
        if url_hostname is None:
            return f'{self.root_url}{url}'
        else:
            if url_hostname==urlparse(self.root_url).hostname:
                return url
            else:
                raise ValueError(f'URL does not match site URL: {url}')