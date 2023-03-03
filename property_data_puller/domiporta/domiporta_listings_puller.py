"""
Module to pull and clean property listings from the Polish property listing site, Domiporta (https://www.domiporta.pl/).

Categories of properties supported are:
- Apartments
- Houses
- Rooms
"""
import os
import yaml
from property_data_puller.property_listings_puller import PropertyListingsPuller


class DomiportaListingsPuller(PropertyListingsPuller):
    """
    Pull property listings from the Polish real estate listing site, Domiporta.
    """
    def __init__(self):
        root_url = 'https://www.domiporta.pl'
        page_param = 'PageNumber'
        data_columns = ['title', 'listing_page_category', 'base_price', 'base_price_num', 'price_utilities_pln_num', 'currency', 'price_zl_per_m2', 'price_zl_per_m2_num', 'surface_area_m2', 'surface_area_m2_num', 'address_locality', 'street_address', 'region', 'country', 'postcode', 'latitude', 'longitude']
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
        listings_list = listings_page_soup.find("div", {"class": "listing"})\
                                          .find("div", {"class": "listing__container"})\
                                          .find("ul", {"class": "grid"})\
                                          .find_all("li", {"class": "grid-item"})
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
        sneakpeek_info = listing_soup.find("div", {"class": "sneakpeak__data"})
        if not sneakpeek_info:
            return
        url = sneakpeek_info.find("a", {"class": "sneakpeak__title"})['href']
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
        listing_details = {}
        header_section = listing_page_soup.find("div", {"class": "detials__header-section"})
        listing_details["title"] = header_section.find("span", {"class": "summary__subtitle-2"}).text.strip()

        # Get the price and currency
        price_info = header_section.find("span", {"class": "summary__price_number"})
        price_number = price_info.find("span", {"itemprop": "price"})
        if price_number:
            listing_details["price"] = price_number["content"]
            listing_details["currency"] = price_info.find("span", {"itemprop": "priceCurrency"})["content"]
        else:
            listing_details["price"] = price_info.text.strip()

        # Extract information from the details section
        details_section = listing_page_soup.find("section", {"class": ["detials__section", "features"]}).find("div", {"class": "features__container"}).find("ul", {"class": "features__list-2"}).find_all("li")
        for item in details_section:
            detail_title = item.find("span", {"class": "features__item_name"})
            if not detail_title: continue
            detail_title = detail_title.text.strip()
            detail_value = item.find("span", {"class": "features__item_value"})

            # Check if the information is known
            if detail_title not in self.listing_details_translations:
                print(f'Unrecognised listing detail: {detail_title.strip()}')
                continue

            # Extract the information depending on which item
            detail_title_trans = self.listing_details_translations[detail_title]
            if detail_title=='Lokalizacja':
                address_details = detail_value.find("span", {"itemprop": "address"})
                listing_details["address_locality"] = address_details.find("span", {"itemprop": "addressLocality"}).text.strip()
                street_address = address_details.find("span", {"itemprop": "streetAddress"})
                if street_address:
                    listing_details["street_address"] = street_address.text.strip()
                region_info = address_details.find("meta", {"itemprop": "addressRegion"})
                if region_info:
                    listing_details["region"] = region_info["content"].strip()
                country_info = address_details.find("meta", {"itemprop": "addressCountry"})
                if country_info:
                    listing_details["country"] = country_info["content"].strip()
                postcode_info = address_details.find("meta", {"itemprop": "postalCode"})
                if postcode_info:
                    listing_details["postcode"] = postcode_info["content"].strip()
                geo = detail_value.find("span", {"itemprop": "geo"})
                if geo:
                    listing_details["latitude"] = geo.find("meta", {"itemprop": "latitude"})["content"].strip()
                    listing_details["longitude"] = geo.find("meta", {"itemprop": "longitude"})["content"].strip()
            elif detail_title in ['Kategoria', 'Przeznaczenie']:
                listing_details[detail_title_trans] = detail_value.find("a").text.strip()
            else:
                listing_details[detail_title_trans] = detail_value.text.strip()

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
        def convert_units_to_num(price, units=None):
            if type(units) is not list: units = [units]
            try:
                for unit in units:
                    price = price.replace(unit, '')
                price_num = float(''.join(price.strip().replace(',','.').split()))
                return price_num
            except:
                return
        data.rename(columns={'price':'base_price'}, inplace=True)
        data['base_price_num'] = data['base_price'].apply(lambda x: convert_units_to_num(x, units='zł'))
        if "price_utilities_pln" in data.columns:
            data['price_utilities_pln_num'] = data['price_utilities_pln'].apply(lambda x: convert_units_to_num(x, units=['PLN', 'zł']))
        data['price_zl_per_m2_num'] = data['price_zl_per_m2'].apply(lambda x: convert_units_to_num(x, units='zł/m'))
        data['surface_area_m2_num'] = data['surface_area_m2'].apply(lambda x: convert_units_to_num(x, units='m2'))
        data['latitude'] = data['latitude'].apply(lambda x: convert_units_to_num(x))
        data['longitude'] = data['longitude'].apply(lambda x: convert_units_to_num(x))

        # Order the columns so that the appending to the data is consistent
        columns_order = ['title', 'listing_page_category', 'base_price', 'base_price_num', 'price_utilities_pln_num', 'currency', 'price_zl_per_m2', 'price_zl_per_m2_num', 'surface_area_m2', 'surface_area_m2_num', 'address_locality', 'street_address', 'region', 'country', 'postcode', 'latitude', 'longitude']
        columns_order += [item for item in self.listing_details_translations.values() if item not in columns_order] + ['url']
        for column in columns_order:
            if column not in data.columns:
                data[column] = ''
        missed_columns = [column for column in data.columns if column not in columns_order]
        if missed_columns:
            raise RuntimeError(f'Missing columns: {missed_columns}')
        data = data[columns_order]

        return data
