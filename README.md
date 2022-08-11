# Web scrape data from Polish property sites

## Introduction
This project is for pulling data from Polish property sites, to show information on the price and availability of residential properties in Poland. It was developed during the response to the Ukraine crisis to fill a gap in information on properties in Poland.

Currently the sites included for pulling data from are:

- Domiporta: https://www.domiporta.pl/
- Otodom: https://www.otodom.pl/
- Olx: https://olx.pl/


## Setup and installation
To install the project, run the following in a bash terminal:

```bash
pip3 install pull_property_listings_poland
```

## Examples
The following is an example of how to pull Domiporta, Olx, and Otodom data for specified listing categories.

```python
from pull_property_listings_poland.domiporta import DomiportaListingsPuller
from pull_property_listings_poland.olx import OlxListingsPuller
from pull_property_listings_poland.otodom import OtodomListingsPuller

# Pull Domiporta data
listings_puller = DomiportaListingsPuller()
listings_puller.pull_listing_categories(data_write_path='domiporta_data.csv',
                                        categories=['apartments', 'houses', 'rooms'])
# Pull Olx data
listings_puller = OlxListingsPuller()
listings_puller.pull_listing_categories(data_write_path='olx_data.csv',
                                        categories=['rooms'])
# Pull Otodom data
listings_puller = OtodomListingsPuller()
listings_puller.pull_listing_categories(data_write_path='otodom_data.csv',
                                        categories=['houses', 'apartments'])
```

## Contact

For more information or support, please contact Alex Howes at alexandra.howes@ifrc.org.
