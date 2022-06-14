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

class PullPropertyListings:
    """
    Class to pull listings from property listing websites and return a dataset.

    Parameters
    ----------
    """
    def __init__(self, root_url, page_param):
        self.root_url = root_url
        self.page_param = page_param


    def pull_listing_categories(self, listing_categories, data_write_path, listing_details_translations, page_start=1, page_end=None):
        """
        Pull listings from multiple listing pages.
        """
        # Print a warning if the file already exists
        if os.path.exists(data_write_path):
            input(f'WARNING: data will overwrite the existing data file at {data_write_path}. Press enter to continue.')
            os.remove(data_write_path)

        # Loop through categories, pull data for each category, and save
        for category_url, category_name in listing_categories.items():
            self.pull_listings(data_write_path=data_write_path,
                               page_slug=category_url,
                               listing_details_translations=listing_details_translations,
                               extra_listing_info={'listing_page_category': category_name},
                               page_start=page_start,
                               page_end=page_end,
                               mode='a',
                               suppress_overwrite_warning=True)


    def pull_listings(self, data_write_path, page_slug, listing_details_translations, extra_listing_info=None, page_start=1, page_end=None, mode='a', suppress_overwrite_warning=False):
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

        listing_details_translations : dict (required)
            Dictionary mapping listing detail names to a translation. The order of keys will also be used to order the columns of the final dataset.

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
        if listing_details_translations is None:
            listing_details_translations = []

        # Loop through listing pages and pull data
        page_number = page_start
        while True:
            data = pd.DataFrame()
            listings_page_url = f'{self.root_url}/{page_slug}?{self.page_param}={page_number}'
            print(f'\nSearching listings in page {page_number}... {listings_page_url}')
            listings_page = requests.get(listings_page_url)
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
                except TypeError as err:
                    print(f'Error with finding the URL for listing {i} on page {listings_page_url}:\n{single_listing}')
                    raise TypeError(err)
                if not single_listing_url:
                    continue
                single_listing_url = f'{self.root_url}{single_listing_url}'
                single_page = requests.get(f'{single_listing_url}')
                single_soup = BeautifulSoup(single_page.content, "html.parser")

                # Extract individual listing information
                try:
                    single_listing_info = self.get_listing_details(listing_page_soup=single_soup,
                                                                   listing_details_translations=listing_details_translations)
                except Exception as err:
                    print(f'Skipping listing due to error: {single_listing_url}')
                    f = open("log.txt", "a")
                    f.write(f'Skipping listing due to error: {single_listing_url}\n')
                    f.close()
                    #raise RuntimeError(err)
                single_listing_info['url'] = single_listing_url

                # Append the data to the dataframe
                data = data.append(single_listing_info, ignore_index=True)

            # Process athe data
            data = self.process_listing_data(listings_data=data,
                                             listing_details_names=listing_details_translations.values())
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
