# Property web scraper

## Introduction
This project is for pulling data from property sites, to show information on the price and availability of residential properties.

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
The following is an example of how to pull Domiporta, Olx, and Otodom data for specified listing categories.

```python
import property_data_scraper

# Pull Hepsiemlak data and save
raw_data_path = 'hepsiemlak_property_data.csv'
listings_puller = property_data_scraper.HepsiemlakListingsPuller()
listings_puller.pull_listings(data_write_path=raw_data_path, 
                              listing_page_slug='kiralik', 
                              get_listing_previews=True,
                              get_listing_pages=True)

# Read in the raw data and process
raw_listings = pd.read_csv(raw_data_path)
processed_listings = listings_puller.process_data(raw_listings)
```

## Contact

For more information or support, please contact Alex Howes at alexandra.howes@ifrc.org.
