"""
Script to pull rental listings for the Polish estate agent website, Domiporta (https://www.domiporta.pl/).

Note that data will be appended to the file in the data folder, so this file should be deleted if you want to create a new file.
"""
import os
import traceback
from urllib.parse import urlparse
import pandas as pd
import requests
from bs4 import BeautifulSoup
import yaml
from collections import Counter


class PullPropertyListings:
    """
    Class to pull listings from property listing websites and return a dataset.

    Parameters
    ----------
    root_url : string (required)
        The root url of the website.

    page_param : string (required)
        The name of the parameter that is in the URL to specify the page number.

    listing_categories : dict (required)
        Dictionary mapping category names to relative URLs for those categories.

    listing_details_translations : dict (required)
        Dictionary mapping listing detail names to a translation. The order of keys will also be used to order the columns of the final dataset.
    """
    def __init__(self, root_url, page_param, listing_categories, listing_details_translations=None):
        self.root_url = root_url
        self.page_param = page_param
        self.listing_categories = listing_categories
        if listing_details_translations is None:
            listing_details_translations = []
        self.listing_details_translations = listing_details_translations


    def pull_listing_categories(self, categories, data_write_path, page_start=1, page_end=None):
        """
        Pull listings from multiple listing pages.

        Parameters
        ----------
        categories : list
            List of categories to pull, e.g. ['houses', 'apartments'].
        """
        # Print a warning if the file already exists
        if os.path.exists(data_write_path):
            input(f'WARNING: data will overwrite the existing data file at {data_write_path}. Press enter to continue.')
            os.remove(data_write_path)

        # Get the categories
        try:
            listing_categories = {category: self.listing_categories[category] for category in categories}
        except KeyError as err:
            raise KeyError(f'Unrecognised listing category {err}')

        # Loop through categories, pull data for each category, and save
        for category_name, category_url in listing_categories.items():
            self.pull_listings(data_write_path=data_write_path,
                               page_slug=category_url,
                               extra_listing_info={'listing_page_category': category_name},
                               page_start=page_start,
                               page_end=page_end,
                               mode='a',
                               suppress_overwrite_warning=True)


    def pull_listings(self, data_write_path, page_slug, extra_listing_info=None, page_start=1, page_end=None, mode='a', suppress_overwrite_warning=False):
        """
        Pull a dataset of listings from the property website and write to a file.
        By default results are appended to the file to enable stopping and starting.

        Parameters
        ----------
        data_write_path : string (required)
            The location of the CSV file to write the dataset of listings to.

        page_slug : string (required)
            A slug to be added to the root url to give the URL of the listings page.

        extra_listing_info : dict (default=None)
            Any extra information to add to the listings dataset, e.g. category information.

        page_start : int (default=1)
            Number of the page to start, starting from 1.

        page_end : int (default=None)
            Number of pages to pull. If None, all pages will be pulled.

        mode : string (default='a')
            Mode used to write the final dataset. Default is append.
        """
        # Check if the write file exists and print a warning
        if not suppress_overwrite_warning:
            if os.path.exists(data_write_path):
                if mode=='a':
                    input(f'WARNING: data will append to the existing data file at {data_write_path}. Press enter to continue.')
                elif mode=='w':
                    input(f'WARNING: data will overwrite the existing data file at {data_write_path}. Press enter to continue.')

        # Loop through listing pages and pull data
        page_number = page_start
        while True:
            data = pd.DataFrame()
            listings_page_url = f'{self.root_url}/{page_slug}?{self.page_param}={page_number}'
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
            if listings_page.history:
                if listings_page.history[0].status_code==301:
                    break

            # Loop through all listings on the page
            for i, single_listing in enumerate(listings):

                # Get the single listing URL and request the single listing page
                try:
                    single_listing_url = self.get_listing_url(single_listing)
                    single_listing_url = self.convert_relative_url(single_listing_url)
                except TypeError as err:
                    print(f'Error with finding the URL for listing {i} on page {listings_page_url}')
                    raise TypeError(err)
                except ValueError as err:
                    continue
                if not single_listing_url:
                    continue
                print(single_listing_url)
                single_page = requests.get(f'{single_listing_url}')
                single_soup = BeautifulSoup(single_page.content, "html.parser")

                # Extract individual listing information
                try:
                    single_listing_info = self.get_listing_details(listing_page_soup=single_soup)
                    single_listing_info['url'] = single_listing_url
                except Exception as err:
                    error_message = f'\nSkipping listing due to error: {single_listing_url}\n{str(err)}'
                    f = open("log.txt", "a")
                    f.write(error_message)
                    f.close()
                    print(err)
                    print(traceback.format_exc())
                    continue

                # Append the data to the dataframe
                data = data.append(single_listing_info, ignore_index=True)

            # Process athe data
            data = self.process_listing_data(data=data)
            if extra_listing_info is not None:
                for name, value in extra_listing_info.items():
                    data[name] = value

            # Save the dataset
            print('Saving data...')
            header = (not os.path.exists(data_write_path)) if mode=='a' else True
            data.to_csv(data_write_path, index=False, header=header, mode=mode)

            if page_end is not None:
                if page_number >= page_end:
                    break
            page_number += 1


    def convert_relative_url(self, url):
        """
        Convert a relative URL to an absolute URL.
        If the URL is an absolute URL of another site, raise an error.
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
