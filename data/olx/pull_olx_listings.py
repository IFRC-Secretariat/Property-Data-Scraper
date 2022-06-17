import sys
import yaml
import json
sys.path.append('..')
from pull_listings import PullPropertyListings


class PullOlxListings(PullPropertyListings):
    """
    Pull property listings from the Polish property listings site, Olx.
    """
    def __init__(self):
        root_url = 'https://www.olx.pl'
        page_param = 'page'
        super().__init__(root_url, page_param)


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
        listings_list = listings_page_soup.find("body")\
                                          .find("div", {"class": "listing-grid-container"})\
                                          .find("div", {"data-testid": "listing-grid"})\
                                          .find_all("div", {"data-cy": "l-card"})
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
        listing_link = listing_soup.find('a', recursive=False)
        if listing_link:
            return listing_link['href']


    def get_listing_details(self, listing_page_soup, listing_details_translations=None):
        """
        Get details of the property listing from the listing soup.

        Parameters
        ----------
        listing_page_soup : BeautifulSoup (required)
            Soup of the listing page.

        listing_details_translations : dict (default=None)
            Dictionary mapping listing detail names to a translation.

        Returns
        -------
        listing_details : dict
            Dictionary mapping listing detail names to content, e.g. {"title": "My listing", "category": "flat"}.
        """
        # Get information from the header
        listing_details = {}
        listing_content = listing_page_soup.find("div", {"class": "css-1wws9er"})
        listing_details["title"] = listing_content.find("h1", {"data-cy": "ad_title"}).text.strip()
        listing_details["price"] = listing_content.find("div", {"data-testid": "ad-price-container"}).find("h3").text.strip()

        # Extract information from the details section
        details_section = listing_content.find("ul").find_all("li")
        if details_section:

            # Get the listing status in the first element
            status = details_section[0].find("p").text.strip()
            if status.lower() not in ['prywatne', 'firmowe']:
                print(f'Unrecognised status: {status}')
            listing_details["status"] = status

            # Get other details
            for detail in details_section[1:]:
                detail_text = detail.find("p").text.strip().split(':')
                detail_title = detail_text[0]
                if detail_title not in listing_details_translations:
                    print(f'Unrecognised listing detail: {detail_title}')
                    continue
                detail_title_trans = listing_details_translations[detail_title]
                listing_details[detail_title_trans] = detail_text[1]

        # Get the latitude and longitude from the script
        scripts = listing_page_soup.find("script", {"id": "olx-init-config"}).string
        lat_loc = scripts.find("lat\\")
        lon_loc = scripts.find("lon\\")
        if (lat_loc>=0) and (lon_loc>=0):
            listing_details["latitude"] = float(scripts[lat_loc+6:lat_loc+20].split(',',1)[0])
            listing_details["longitude"] = float(scripts[lon_loc+6:lon_loc+20].split(',',1)[0])

        return listing_details


    def process_listing_data(self, listings_data, listing_details_names):
        """
        Process the dataset of listings.

        Parameters
        ----------
        listings_data : Pandas DataFrame (required)
            Pandas DataFrame with one row per listing.
        """
        # Process the data to convert numbers with units to just numbers
        def convert_units_to_num(price, unit=None):
            try:
                price_num = float(str(price).strip().split(unit)[0].replace(',','.').replace(' ',''))
                return price_num
            except:
                return
        listings_data['price_num'] = listings_data['price'].apply(lambda x: convert_units_to_num(x, unit='zł'))
        listings_data['latitude'] = listings_data['latitude'].apply(lambda x: convert_units_to_num(x))
        listings_data['longitude'] = listings_data['longitude'].apply(lambda x: convert_units_to_num(x))

        # Order the columns so that the appending to the data is consistent
        columns_order = ['title', 'price', 'price_num', 'latitude', 'longitude', 'status']
        columns_order += [item for item in listing_details_names if item not in columns_order]
        if 'listing_page_category' in listings_data.columns:
            columns_order += ['listing_page_category']
        columns_order += ['url']
        for column in columns_order:
            if column not in listings_data.columns:
                listings_data[column] = ''
        missed_columns = [column for column in listings_data.columns if column not in columns_order]
        if missed_columns:
            raise RuntimeError(f'Missing columns: {missed_columns}')
        listings_data = listings_data[columns_order]

        return listings_data


if __name__ == "__main__":
    listing_categories = {'d/nieruchomosci/stancje-pokoje/': 'rooms'}
    listings_puller = PullOlxListings()
    listings_puller.pull_listing_categories(data_write_path='raw/2022-06-14_olx_listings.csv',
                                            listing_categories=listing_categories,
                                            listing_details_translations=yaml.safe_load(open('listing_details_translations.yml')),
                                            page_start=1)
