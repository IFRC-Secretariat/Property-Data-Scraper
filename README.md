# Property Data Scraper

## Introduction
This project is for web scraping data from property sites, to show information on the price and availability of properties.

Currently the sites included for pulling data from are:

- Poland:
    - Domiporta: https://www.domiporta.pl/
    - Otodom: https://www.otodom.pl/
    - Olx: https://olx.pl/
- Türkiye:
    - Hepsiemlak: https://hepsiemlak.com/ 
    - Emlakjet: https://www.emlakjet.com/
    - Zingat: https://www.zingat.com/


## Setup and installation
To install the project, run the following in a bash terminal from the top-level of the project:

```bash
pip3 install .
```

## Examples
The following examples show how to pull data from the different listing sites. There is a class for each listing site. For each one, the ```pull_listings``` method can be used to pull the listings. This has the same parameters for each class:

- data_write_path : string (required). Location and filename (CSV) to save the data to. This is required becuase the data is saved for each page of listings, so that there is data saved even if the program stops running before finishing.

- listing_page_slug : string (required). The string to add to the root URL to get the listings page URL.

- get_listing_previous: boolean (default=True). If True, information will be extracted from the listing preview information on the listings page.

- get_listing_pages : boolean (default=True). If True, each single listing page will be requested and information will be extracted from it.

- page_start : int (default=1). The page number to start at.

- page_end : int or None (default=None). Number of pages to pull. If None, all pages will be pulled.

### Poland dataz

```python
import property_data_scraper

"""
Get Domiporta data
"""
# Pull Domiporta data and save
domiporta_raw_data_path = 'domiporta_property_data_raw.csv'
listings_puller = property_data_scraper.DomiportaListingsPuller()
listings_puller.pull_listings(
    data_write_path=domiporta_raw_data_path, 
    listing_page_slug='kirmieszkanie/wynajmealik',
    get_listing_previews=False,
    get_listing_pages=True
)
# Read in the raw data, process, and save
raw_listings = pd.read_csv(domiporta_raw_data_path)
processed_listings = listings_puller.process_data(raw_listings)
processed_listings.to_csv('domiporta_property_data_processed.csv', index=False)

"""
Get Otodom data
"""
# Pull Otodom data and save
otodom_raw_data_path = 'otodom_property_data_raw.csv'
listings_puller = property_data_scraper.OtodomListingsPuller()
listings_puller.pull_listings(
    data_write_path=otodom_raw_data_path, 
    listing_page_slug='pl/oferty/wynajem/mieszkanie/cala-polska',
    get_listing_previews=False,
    get_listing_pages=True
)
# Read in the raw data, process, and save
raw_listings = pd.read_csv(otodom_raw_data_path)
processed_listings = listings_puller.process_data(raw_listings)
processed_listings.to_csv('otodom_property_data_processed.csv', index=False)

"""
Get Olx data
"""
# Pull Olx data and save
olx_raw_data_path = 'olx_property_data_raw.csv'
listings_puller = property_data_scraper.OlxListingsPuller()
listings_puller.pull_listings(
    data_write_path=olx_raw_data_path, 
    listing_page_slug='nieruchomosci/mieszkania/',
    get_listing_previews=False,
    get_listing_pages=True
)
# Read in the raw data, process, and save
raw_listings = pd.read_csv(olx_raw_data_path)
processed_listings = listings_puller.process_data(raw_listings)
processed_listings.to_csv('olx_property_data_processed.csv', index=False)

```

### Türkiye data

```python
import property_data_scraper

"""
Get Hepsiemlak data
"""
# Pull Hepsiemlak data and save
hepsiemlak_raw_data_path = 'hepsiemlak_property_data_raw.csv'
listings_puller = property_data_scraper.HepsiemlakListingsPuller()
listings_puller.pull_listings(
    data_write_path=hepsiemlak_raw_data_path, 
    listing_page_slug='kiralik', 
    get_listing_previews=True,
    get_listing_pages=True
)
# Read in the raw data, process, and save
raw_listings = pd.read_csv(hepsiemlak_raw_data_path)
processed_listings = listings_puller.process_data(raw_listings)
processed_listings.to_csv('hepsiemlak_property_data_processed.csv', index=False)

"""
Get Emlakjet data
"""
# Pull Emlakjet data and save
emlakjet_raw_data_path = 'emlakjet_property_data_raw.csv'
listings_puller = property_data_scraper.EmlakjetListingsPuller()
listings_puller.pull_listings(
    data_write_path=emlakjet_raw_data_path, 
    listing_page_slug='kiralik-konut', 
    get_listing_previews=True,
    get_listing_pages=False
)
# Read in the raw data and process
raw_listings = pd.read_csv(emlakjet_raw_data_path)
processed_listings = listings_puller.process_data(raw_listings)
processed_listings.to_csv('emlakjet_property_data_processed.csv', index=False)

"""
Get Zingat data
"""
# Pull Zingat data and save
zingat_raw_data_path = 'zingat_property_data_raw.csv'
listings_puller = property_data_scraper.ZingatListingsPuller()
listings_puller.pull_listings(
    data_write_path=zingat_raw_data_path, 
    listing_page_slug='kiralik', 
    get_listing_previews=False,
    get_listing_pages=True
)
# Read in the raw data and process
raw_listings = pd.read_csv(zingat_raw_data_path)
processed_listings = listings_puller.process_data(raw_listings)
processed_listings.to_csv('zingat_property_data_processed.csv', index=False)

```

## Contact

For more information or support, please contact Alex Howes at alexandra.howes@ifrc.org.
