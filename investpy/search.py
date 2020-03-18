# Copyright 2018-2020 Alvaro Bartolome @ alvarobartt in GitHub
# See LICENSE for details.

import requests

import re

from .utils.search_obj import SearchObj
from .utils.user_agent import get_random


def search(text, filters=None, n_results=None):
    """
    This function will use the Investing search engine so to retrieve the search results of the
    introduced text. This function will create a :obj:`list` of :obj:`investpy.utils.search_obj.SearchObj`
    class instances which will contain the search results so that they can be easily accessed and so
    to ease the data retrieval process since it can be done calling the methods `self.retrieve_recent_data()`
    or `self.retrieve_historical_data(from_date, to_date)` from the class instance, which will fill the `self.data`
    attribute of that class instance.

    Args:
        text (:obj:`str`): text to search in Investing among all its indexed data.
        filters (:obj:`list` of :obj:`str`, optional):
            list with the filter/s to be applied to the search result quotes so that the resulting quotes match
            the filters. Possible filters are: `indices`, `stocks`, `etfs`, `funds`, `commodities`, `currencies`, 
            `crypto`, `bonds`, `certificates` and `fxfutures`. Default is `None` which means that no filter will 
            be applied.
        n_results (:obj:`int`, optional): number of search results to retrieve and return from Investing.

    Returns:
        :obj:`list` of :obj:`investpy.utils.search_obj.SearchObj`:
            The resulting :obj:`list` of :obj:`investpy.utils.search_obj.SearchObj` will contained the retrieved
            financial products matching the introduced text as indexed in Investing, if found. Note that if no
            information was found this function will raise a `ValueError` exception.

    Raises:
        ValueError: raised if either the introduced text is not valid or if no results were found for that text.
        ConnectionError: raised whenever the connection to Investing.com errored (did not return a 200 OK code).

    """

    if not text:
        raise ValueError('ERR#0074: text parameter is mandatory and it should be a valid str.')

    if not isinstance(text, str):
        raise ValueError('ERR#0074: text parameter is mandatory and it should be a valid str.')

    if n_results and not isinstance(n_results, int):
        raise ValueError('ERR#0088: n_results parameter is optional, but if specified, it must be an integer equal or higher than 1.')

    if n_results is not None:
        if n_results < 1:
            raise ValueError('ERR#0088: n_results parameter is optional, but if specified, it must be an integer higher than 0.')

    if filters and not isinstance(filters, list):
        raise ValueError('ERR#0094: filters parameter can just be a list or None if no filter wants to be applied.')

    available_filters = {
        'indices': 'indice', 
        'stocks': 'equities', 
        'etfs': 'etf', 
        'funds': 'fund', 
        'commodities': 'commodity', 
        'currencies': 'currency', 
        'cryptos': 'crypto', 
        'bonds': 'bond', 
        'certificates': 'certificate', 
        'fxfutures': 'fxfuture'
    }

    if filters:
        condition = set(filters).issubset(available_filters.keys())
        if condition is False:
            raise ValueError('ERR#0095: filters parameter values must be contained in ' + ', '.join(available_filters) + '.')
        else:
            filters = [available_filters[filter_] for filter_ in filters]
    else:
        filters = [value for key, value in available_filters.items()]

    params = {
        'search_text': text,
        'tab': 'quotes',
        'limit': 270,
        'offset': 0
    }

    head = {
        "User-Agent": get_random(),
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "text/html",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    url = 'https://www.investing.com/search/service/SearchInnerPage'

    search_results = list()

    total_results = None

    while True:
        req = requests.post(url, headers=head, data=params)

        if req.status_code != 200:
            raise ConnectionError("ERR#0015: error " + str(req.status_code) + ", try again later.")

        data = req.json()

        if data['total']['quotes'] == 0:
            raise ValueError("ERR#0093: no results found on Investing for the introduced text.")

        if total_results is None:
            total_results = data['total']['quotes']

        if n_results is None:
            n_results = data['total']['quotes']

        for quote in data['quotes']:
            country = quote['flag'].lower()
            country = country if country not in ['usa', 'uk'] else 'united states' if country == 'usa' else 'united kingdom'

            tag = re.sub(r'\/(.*?)\/', '', quote['link'])

            if quote['pair_type'] in filters:
                search_results.append(SearchObj(id_=quote['pairId'], name=quote['name'], symbol=quote['symbol'],
                                                country=country, tag=tag, pair_type=quote['pair_type'], exchange=quote['exchange']))
        
        params['offset'] = len(search_results) - 1                    
        
        if len(search_results) >= n_results or len(search_results) >= total_results:
            break
        
    return list(set(search_results))[:n_results]
