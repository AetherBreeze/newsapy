import aiohttp
import asyncio
import hashlib

from newsapy import const
from newsapy.newsapi_auth import NewsApiAuth
from newsapy.newsapi_article import NewsArticle
from newsapy.nltk_handler import initialize_nltk_data
from os.path import isdir
from os import mkdir
from sys import version_info



class NewsApiClient(object):
    def __init__(self, api_keys_file_path):
        with open(api_keys_file_path, "r") as f: # this file stores newsapy account data in a [firstname/username/password/api key] format
            self.api_keys = [line.split('/')[3].strip('\n') for line in f.readlines()] # extract just the api keys, then store them
        self.auth = NewsApiAuth(api_key=self.api_keys[0])
        self.current_api_key_index = 0
        self.__consecutive_key_failures = 0

        if not isdir(const.IMAGE_DIRECTORY):
            mkdir(const.IMAGE_DIRECTORY)
        self.event_loop = asyncio.get_event_loop()
        self.http_session = aiohttp.ClientSession()
        self.hasher = hashlib.sha3_224()

        initialize_nltk_data() # ensures that all the data needed for proper noun extraction is downloaded

    def __switch_api_keys(self, forever=False):
        if self.__consecutive_key_failures == len(self.api_keys) + 1: # plus one means "see if the first key has cooled down before exploding"
            raise Exception("[ERROR] All {} provided NewsAPI keys are on ratelimit. Impressive!".format(len(self.api_keys)))

        if self.current_api_key_index == len(self.api_keys) - 1: # if were at the end of the list of api keys
            self.current_api_key_index = 0 # cycle back to the start
        else: # otherwise,
            self.current_api_key_index += 1 # go to the next api key

        self.auth = NewsApiAuth(api_key=self.api_keys[self.current_api_key_index]) # refreshing key means we have to change the auth headers
        if not forever: # unless we were specifically told to infinitely loop over ratelimited api keys until one cools down,
            self.__consecutive_key_failures += 1 # remember that this key was limited

    def get_top_headlines(self, q=None, sources=None, language='en', country=None, category=None,
                                      page_size=20, page=None, force_initialize_proper_nouns=False, query_results_tuple=False):
        return self.event_loop.run_until_complete(self.get_top_headlines_async(q=q, sources=sources, language=language, country=country, category=category, page_size=page_size, page=page, force_initialize_proper_nouns=force_initialize_proper_nouns, query_results_tuple=query_results_tuple))

    async def get_top_headlines_async(self, q=None, sources=None, language='en', country=None, category=None, page_size=20,
                          page=None, force_initialize_proper_nouns=False, query_results_tuple=None):
        """
            Returns live top and breaking headlines for a country, specific category in a country, single source, or multiple sources..

            Optional parameters:
                (str) q - return headlines w/ specific keyword or phrase. For example:
                          'bitcoin', 'trump', 'tesla', 'ethereum', etc.

                (str) sources - return headlines of news sources! some Valid values are:
                                'bbc-news', 'the-verge', 'abc-news', 'crypto coins news',
                                'ary news','associated press','wired','aftenposten','australian financial review','axios',
				'bbc news','bild','blasting news','bloomberg','business insider','engadget','google news',
				'hacker news','info money,'recode','techcrunch','techradar','the next web','the verge' etc.

		(str) language - The 2-letter ISO-639-1 code of the language you want to get headlines for. Valid values are:
				 'ar','de','en','es','fr','he','it','nl','no','pt','ru','se','ud','zh'

                (str) country - The 2-letter ISO 3166-1 code of the country you want to get headlines! Valid values are:
                                'ae','ar','at','au','be','bg','br','ca','ch','cn','co','cu','cz','de','eg','fr','gb','gr',
                                'hk','hu','id','ie','il','in','it','jp','kr','lt','lv','ma','mx','my','ng','nl','no','nz',
                                'ph','pl','pt','ro','rs','ru','sa','se','sg','si','sk','th','tr','tw','ua','us'

		(str) category - The category you want to get headlines for! Valid values are:
				 'business','entertainment','general','health','science','sports','technology'

		(int) page_size - The number of results to return per page (request). 20 is the default, 100 is the maximum.

		(int) page - Use this to page through the results if the total results found is greater than the page size.
        """

        # Define Payload
        payload = {}

        # Keyword/Phrase
        if q is not None:
            if version_info[0] == 3:
                from urllib.parse import quote
                q_is_str = isinstance(q, str)
            elif version_info[0] == 2:
                from urllib import quote
                q_is_str = isinstance(q, basestring)
            else:
                raise SystemError("unsupported version of python detected (supported versions: 2, 3)")

            if q_is_str:
                payload['q'] = quote(q)
            else:
                raise TypeError('keyword/phrase q param should be of type str')

        # Sources
        if (sources is not None) and ((country is not None) or (category is not None)):
            raise ValueError('cannot mix country/category param with sources param.')

        # Sources
        if sources is not None:
            if type(sources) == str:
                sources = [sources]
            if type(sources) == list:
                payload['sources'] = ','.join(sources)
            else:
                raise TypeError('sources param should be of a list of type str')

        # Language
        if language is not None:
            if type(language) == str:
                if language in const.languages:
                    payload['language'] = language
                else:
                    raise ValueError('invalid language')
            else:
                raise TypeError('language param should be of type str')

        # Country
        if country is not None:
            if type(country) == str:
                if country in const.countries:
                    payload['country'] = country
                else:
                    raise ValueError('invalid country')
            else:
                raise TypeError('country param should be of type str')

        # Category
        if category is not None:
            if type(category) == str:
                if category in const.categories:
                    payload['category'] = category
                else:
                    raise ValueError('invalid category')
            else:
                raise TypeError('category param should be of type str')

        # Page Size
        if page_size is not None:
            if type(page_size) == int:
                if 0 <= page_size <= 100:
                    payload['pageSize'] = page_size
                else:
                    raise ValueError('page_size param should be an int between 1 and 100')
            else:
                raise TypeError('page_size param should be an int')

        # Page
        if page is not None:
            if type(page) == int:
                if page > 0:
                    payload['page'] = page
                else:
                    raise ValueError('page param should be an int greater than 0')
            else:
                raise TypeError('page param should be an int')

        # Send Request
        async with (await self.http_session.get(const.TOP_HEADLINES_URL, headers=self.auth(), timeout=30, params=payload)) as request:
            reply_json = await request.json()
            if request.status != const.HTTP_OK: # if the request failed, this usually means were ratlimited #TODO: Make this catch timeout errors *only*, so it doesnt trigger when the internet goes down
                self.__switch_api_keys()
                return await self.get_top_headlines_async(q=q, sources=sources, language=language, country=country, category=category, page_size=page_size, page=page, force_initialize_proper_nouns=force_initialize_proper_nouns, query_results_tuple=query_results_tuple)

        self.__consecutive_key_failures = 0 # once the request works, we know we have at least one working api key
        articles = [NewsArticle(self, article, force_initialize_proper_nouns=force_initialize_proper_nouns) for article
                    in reply_json["articles"]]
        if query_results_tuple:  # usually to keep track of queries when sending multiple requests at once
            if q and query_results_tuple == "keyword": # if we were told to group articles with keywords
                return q, articles
            if query_results_tuple == "source": # if we were told to group articles with sources
                return sources[0], articles # assume this is only called when theres only one source
        else:
            return articles

    def get_everything(self, q=None, sources=None, domains=None, exclude_domains=None,
                       from_param=None, to=None, language='en', sort_by=None, page=None,
                       page_size=20, force_initialize_proper_nouns=False, query_results_tuple=False):
        return self.event_loop.run_until_complete(self.get_everything_async(q=q, sources=sources, domains=domains, exclude_domains=exclude_domains, from_param=from_param, to=to, language=language,
                                                                            sort_by=sort_by, page=page, page_size=page_size, force_initialize_proper_nouns=force_initialize_proper_nouns, query_results_tuple=query_results_tuple))

    async def get_everything_async(self, q=None, sources=None, domains=None, exclude_domains=None,
                       from_param=None, to=None, language='en', sort_by=None, page=None,
                       page_size=20, force_initialize_proper_nouns=False, query_results_tuple=None):
        """
            Search through millions of articles from over 5,000 large and small news sources and blogs.

            Optional parameters:
                (str) q - return headlines w/ specified coin! Valid values are:
                            'bitcoin', 'trump', 'tesla', 'ethereum', etc

                (str) sources - return headlines of news sources! some Valid values are:
                            'bbc-news', 'the-verge', 'abc-news', 'crypto coins news',
                            'ary news','associated press','wired','aftenposten','australian financial review','axios',
			    'bbc news','bild','blasting news','bloomberg','business insider','engadget','google news',
		  	    'hacker news','info money,'recode','techcrunch','techradar','the next web','the verge' etc.

		(str) domains - A comma-seperated string of domains (eg bbc.co.uk, techcrunch.com, engadget.com) to restrict the search to.

        (str) exclude_domains - A comma_seperated string of domains to be excluded from the search

		(str) from_param - A date and optional time for the oldest article allowed.
                                       (e.g. 2018-03-05 or 2018-03-05T03:46:15)

		(str) to - A date and optional time for the newest article allowed.

		(str) language - The 2-letter ISO-639-1 code of the language you want to get headlines for. Valid values are:
				'ar','de','en','es','fr','he','it','nl','no','pt','ru','se','ud','zh'

		(str) sort_by - The order to sort the articles in. Valid values are: 'relevancy','popularity','publishedAt'

		(int) page_size - The number of results to return per page (request). 20 is the default, 100 is the maximum.

		(int) page - Use this to page through the results if the total results found is greater than the page size.
        """

        # Define Payload
        payload = {}

        # Keyword/Phrase
        if q is not None:
            if version_info[0] == 3:
                from urllib.parse import quote
                q_is_str = isinstance(q, str)
            elif version_info[0] == 2:
                from urllib import quote
                q_is_str = isinstance(q, basestring)
            else:
                raise SystemError("unsupported version of python detected (supported versions: 2, 3)")

            if q_is_str:
                payload['q'] = quote(q)
            else:
                raise TypeError('keyword/phrase q param should be of type str')

        # Sources
        if sources is not None:
            if type(sources) == str:
                sources = [sources]
            if type(sources) == list:
                payload['sources'] = ','.join(sources)
            else:
                raise TypeError('sources param should be of a list of type str')

        # Domains To Search
        if domains is not None:
            if type(domains) == str:
                payload['domains'] = domains
            else:
                raise TypeError('domains param should be of type str')

        if exclude_domains is not None:
            if isinstance(exclude_domains, str):
                payload['excludeDomains'] = exclude_domains
            else:
                raise TypeError('exclude_domains param should be of type str')

        # Search From This Date ...
        if from_param is not None:
            if type(from_param) == str:
                if (len(from_param)) >= 10:
                    for i in range(len(from_param)):
                        if (i == 4 and from_param[i] != '-') or (i == 7 and from_param[i] != '-'):
                            raise ValueError('from_param should be in the format of YYYY-MM-DD')
                        else:
                            payload['from'] = from_param
                else:
                    raise ValueError('from_param should be in the format of YYYY-MM-DD')
            else:
                raise TypeError('from_param should be of type str')

        # ... To This Date
        if to is not None:
            if type(to) == str:
                if (len(to)) >= 10:
                    for i in range(len(to)):
                        if (i == 4 and to[i] != '-') or (i == 7 and to[i] != '-'):
                            raise ValueError('to should be in the format of YYYY-MM-DD')
                        else:
                            payload['to'] = to
                else:
                    raise ValueError('to param should be in the format of YYYY-MM-DD')
            else:
                raise TypeError('to param should be of type str')

        # Language
        if language is not None:
            if type(language) == str:
                if language not in const.languages:
                    raise ValueError('invalid language')
                else:
                    payload['language'] = language
            else:
                raise TypeError('language param should be of type str')

        # Sort Method
        if sort_by is not None:
            if type(sort_by) == str:
                if sort_by in const.sort_method:
                    payload['sortBy'] = sort_by
                else:
                    raise ValueError('invalid sort')
            else:
                raise TypeError('sort_by param should be of type str')

        # Page Size
        if page_size is not None:
            if type(page_size) == int:
                if 0 <= page_size <= 100:
                    payload['pageSize'] = page_size
                else:
                    raise ValueError('page_size param should be an int between 1 and 100')
            else:
                raise TypeError('page_size param should be an int')

        # Page
        if page is not None:
            if type(page) == int:
                if page > 0:
                    payload['page'] = page
                else:
                    raise ValueError('page param should be an int greater than 0')
            else:
                raise TypeError('page param should be an int')

        # Send Request

        async with self.http_session.get(const.EVERYTHING_URL, headers=self.auth(), timeout=30, params=payload) as request:
            reply_json = await request.json()
            # Check Status of Request
            if request.status != const.HTTP_OK:
                self.__switch_api_keys()
                return await self.get_everything_async(q=q, sources=sources, language=language, domains=domains, exclude_domains=exclude_domains, from_param=from_param, to=to, sort_by=sort_by, page_size=page_size, page=page, force_initialize_proper_nouns=force_initialize_proper_nouns, query_results_tuple=query_results_tuple)

        self.__consecutive_key_failures = 0 # once a request works, we know we have at least one working key
        articles = [NewsArticle(self, article, force_initialize_proper_nouns=force_initialize_proper_nouns) for article in reply_json["articles"]]
        if query_results_tuple: #  usually to keep track of queries or sources when sending multiple requests at once
            if q and query_results_tuple == "keyword": # if we were told to group articles with keywords
                return q, articles
            if query_results_tuple == "source": # if we were told to group articles with sources
                return sources[0], articles # assume this is only called when theres only one source
        else:
            return articles

    def get_sources(self, category=None, language='en', country=None):
        return self.event_loop.run_until_complete(self.get_sources_async(category=category, language=language, country=country))

    async def get_sources_async(self, category=None, language='en', country=None):
        """
            Returns the subset of news publishers that top headlines...

            Optional parameters:
                (str) category - The category you want to get headlines for! Valid values are:
				 'business','entertainment','general','health','science','sports','technology'

		(str) language - The 2-letter ISO-639-1 code of the language you want to get headlines for. Valid values are:
				'ar','de','en','es','fr','he','it','nl','no','pt','ru','se','ud','zh'

                (str) country - The 2-letter ISO 3166-1 code of the country you want to get headlines! Valid values are:
                                'ae','ar','at','au','be','bg','br','ca','ch','cn','co','cu','cz','de','eg','fr','gb','gr',
                                'hk','hu','id','ie','il','in','it','jp','kr','lt','lv','ma','mx','my','ng','nl','no','nz',
                                'ph','pl','pt','ro','rs','ru','sa','se','sg','si','sk','th','tr','tw','ua','us'

				(str) category - The category you want to get headlines for! Valid values are:
						'business','entertainment','general','health','science','sports','technology'

        """

        # Define Payload
        payload = {}

        # Language
        if language is not None:
            if type(language) == str:
                if language in const.languages:
                    payload['language'] = language
                else:
                    raise ValueError('invalid language')
            else:
                raise TypeError('language param should be of type str')

        # Country
        if country is not None:
            if type(country) == str:
                if country in const.countries:
                    payload['country'] = country
                else:
                    raise ValueError('invalid country')
            else:
                raise TypeError('country param should be of type str')

                # Category
        if category is not None:
            if type(category) == str:
                if category in const.categories:
                    payload['category'] = category
                else:
                    raise ValueError('invalid category')
            else:
                raise TypeError('category param should be of type str')

        # Send Request
        async with self.http_session.get(const.SOURCES_URL, headers=self.auth(), timeout=30, params=payload) as request:
            # Check Status of Request
            reply_json = await request.json()
            if request.status != const.HTTP_OK:
                self.__switch_api_keys()
                return await self.get_sources_async(language=language, country=country, category=category)

        self.__consecutive_key_failures = 0 # one the request works, we know we have at least one working api key
        return reply_json

    def simultaneous_source_search_from_keyword(self, news_sources, keyword, search_type="everything", **kwargs): # returns a dictionary of the form (source, results_from_source)
        ret = {}
        if search_type == "top_headlines":
            source_article_list_pairs = self.event_loop.run_until_complete(
                self.run_requests_async([(news_source, self.get_top_headlines_async(q=keyword, sources=[news_source], query_results_tuple="source", **kwargs)) for news_source in news_sources]))
        else:
            source_article_list_pairs = self.event_loop.run_until_complete(
                self.run_requests_async([(news_source, self.get_everything_async(q=keyword, sources=[news_source], query_results_tuple="source", **kwargs))for news_source in news_sources]))
        for source, article_list in source_article_list_pairs:
            ret[source] = article_list

        return ret

    def simultaneous_keyword_search_from_sources(self, keywords, news_sources, search_type="everything", **kwargs): # returns (keyword, results_about_keyword) pairs to keep track of response-keyword pairs
        ret = {}
        if search_type == "top_headlines":
            top_headlines_for_each_keyword = self.event_loop.run_until_complete(
                self.run_requests_async([self.get_top_headlines_async(q=keyword, sources=news_sources, query_results_tuple="keyword", **kwargs) for keyword in keywords]))
        else:
            top_headlines_for_each_keyword = self.event_loop.run_until_complete(
                self.run_requests_async([self.get_everything_async(q=keyword, sources=news_sources, query_results_tuple="keyword", **kwargs) for keyword in keywords]))

        for keyword, article_list in top_headlines_for_each_keyword: # get_top_headlines returns a (query, list_of_results) pair
            ret[keyword] = article_list

        return ret


    async def run_requests_async(self, requests_list):
        return asyncio.gather(*requests_list)

    def run_requests(self, requests_list):
        return self.event_loop.run_until_complete(self.run_requests_async(requests_list))

    async def get_images_of_articles_async(self, articles_list, dimensions=None, save_path="images"):
        image_futures = [article.image_async(dimensions=dimensions, save_path=save_path) for article in articles_list] # collect the async image fetching tasks of every article in the list
        return self.run_requests_async(image_futures) #

    def get_images_of_articles(self, articles_list, dimensions=None, save_path="images"):
        return self.event_loop.run_until_complete(self.get_images_of_articles_async(articles_list, dimensions=dimensions, save_path=save_path))

    def close(self):
        self.event_loop.run_until_complete(self.http_session.close())