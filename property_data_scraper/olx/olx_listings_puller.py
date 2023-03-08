"""
Module to pull and clean property listings from the Polish property listing site, Olx (https://www.olx.pl/).

Categories of properties supported are:
- Rooms
"""
import os
import yaml
from property_data_scraper.property_listings_puller import PropertyListingsPuller


class OlxListingsPuller(PropertyListingsPuller):
    """
    Pull property listings from the Polish property listings site, Olx.
    """
    def __init__(self):
        root_url = 'https://www.olx.pl'
        page_param = 'page'
        data_columns = ['title', 'price', 'price_num', 'latitude', 'longitude', 'status', 'listing_page_category']
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        listing_details_translations = yaml.safe_load(open(os.path.join(__location__, 'listing_details_translations.yml'), encoding='utf-8'))
        super().__init__(root_url=root_url,
                         page_param=page_param,
                         data_columns=data_columns,
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
                if detail_title not in self.listing_details_translations:
                    print(f'Unrecognised listing detail: {detail_title}')
                    continue
                detail_title_trans = self.listing_details_translations[detail_title]
                listing_details[detail_title_trans] = detail_text[1]

        # Get the latitude and longitude from the script
        scripts = listing_page_soup.find("script", {"id": "olx-init-config"}).string
        lat_loc = scripts.find("lat\\")
        lon_loc = scripts.find("lon\\")
        if (lat_loc>=0) and (lon_loc>=0):
            listing_details["latitude"] = float(scripts[lat_loc+6:lat_loc+20].split(',',1)[0])
            listing_details["longitude"] = float(scripts[lon_loc+6:lon_loc+20].split(',',1)[0])

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
        # Process the data to convert numbers with units to just numbers
        def convert_units_to_num(price, unit=None):
            try:
                price_num = float(str(price).strip().split(unit)[0].replace(',','.').replace(' ',''))
                return price_num
            except:
                return
        data['price_num'] = data['price'].apply(lambda x: convert_units_to_num(x, unit='zł'))
        data['latitude'] = data['latitude'].apply(lambda x: convert_units_to_num(x))
        data['longitude'] = data['longitude'].apply(lambda x: convert_units_to_num(x))

        # Order the columns so that the appending to the data is consistent
        columns_order = ['title', 'price', 'price_num', 'latitude', 'longitude', 'status', 'listing_page_category']
        columns_order += [item for item in self.listing_details_translations.values() if item not in columns_order]
        columns_order += ['url']
        for column in columns_order:
            if column not in data.columns:
                data[column] = ''
        missed_columns = [column for column in data.columns if column not in columns_order]
        if missed_columns:
            raise RuntimeError(f'Missing columns: {missed_columns}')
        data = data[columns_order]

        return data
