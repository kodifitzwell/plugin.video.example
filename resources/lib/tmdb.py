import requests
from requests.adapters import HTTPAdapter

from resources.external.simpleplugin import Addon, Plugin
from resources.external import tmdbsimple as TMDB
#from resources.lib import common


addon, plugin = Addon(), Plugin()

session = requests.Session()
session.mount('https://api.themoviedb.org', HTTPAdapter(pool_maxsize=100))

EXPIRES_24_HOURS = 60*24
TMDB.REQUESTS_SESSION = session
TMDB.REQUESTS_TIMEOUT = (2.05, 4.05)
#TMDB.API_KEY = ''

prop = addon.get_mem_storage(addon.name)
try: TMDB.API_KEY = prop['tmdb_api_key']
except: TMDB.API_KEY = prop['tmdb_api_key'] = addon.get_setting('tmdb_api_key')
try: IMAGE_RES = prop['tmdb_images']
except: IMAGE_RES = prop['tmdb_images'] = addon.get_setting('tmdb_images')


class TmdbImages:
	images_url = 'https://image.tmdb.org/t/p'
	backdrop_sizes = ['w780', 'w300', 'original', 'w1280']
	poster_sizes = ['w500', 'w342', 'original', 'w780']
	logo_sizes = ['w300', 'w185' , 'original', 'w500']
	_mapping = {'medium': 0, 'low': 1, 'original': 2, 'high': 3}

	def __init__(self, path=None, res=None):
		self.path = path
		if isinstance(res, str): res = self._mapping[res]
		self.res = res if isinstance(res, int) else IMAGE_RES

	@property
	def fanart_url(self):
		if self.path == '': return ''
		return f"{self.images_url}/{self.backdrop_sizes[self.res]}{self.path or ''}"

	@property
	def poster_url(self):
		if self.path == '': return ''
		return f"{self.images_url}/{self.poster_sizes[self.res]}{self.path or ''}"

	@property
	def logo_url(self):
		if self.path == '': return ''
		return f"{self.images_url}/{self.logo_sizes[self.res]}{self.path or ''}"


@plugin.mem_cached(EXPIRES_24_HOURS)
def trending_tv(page):
	params = {'page': page, 'with_original_language': 'en'}
	response = TMDB.Trending('tv', 'week').info(**params)
	return response, 'tvshows'


@plugin.mem_cached(EXPIRES_24_HOURS)
def popular_tv(page):
	params = {'page': page, 'with_original_language': 'en'}
	response = TMDB.Discover().tv(**params)
	return response, 'tvshows'


@plugin.mem_cached(EXPIRES_24_HOURS)
def latest_tv(page): # requires at least one vote, attempt to filter junk
	from datetime import datetime, timedelta

	date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
	params = {
		'page': page,
		'air_date.lte': date,
		'region': 'US',
		'vote_count.gte': 1,
		'with_original_language': 'en',
		'sort_by': 'primary_release_date.desc'}
	response = TMDB.Discover().tv(**params)
	return response, 'tvshows'


@plugin.mem_cached(EXPIRES_24_HOURS)
def trending_movies(page):
	params = {'page': page, 'with_original_language': 'en'}
	response = TMDB.Trending('movie', 'week').info(**params)
	return response, 'movies'


@plugin.mem_cached(EXPIRES_24_HOURS)
def popular_movies(page):
	params = {'page': page, 'region': 'US', 'with_original_language': 'en'}
	response = TMDB.Discover().movie(**params)
	return response, 'movies'


@plugin.mem_cached(EXPIRES_24_HOURS)
def latest_digital(page): # requires at least one vote, attempt to filter junk
	from datetime import datetime, timedelta

	date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
	params = {
		'page': page,
		'release_date.lte': date,
		'region': 'US',
		'vote_count.gte': 1,
		'with_original_language': 'en',
		'with_release_type': '4|5|6',
		'sort_by': 'primary_release_date.desc'}
	response = TMDB.Discover().movie(**params)
	return response, 'movies'


def OLD_SEARCH_TV(page):
	import xbmcgui

	pages_max = addon.get_setting('tmdb_pages')
	response = {'page': page, 'total_pages': page, 'results': []}
	query = xbmcgui.Dialog().input('TV Search')
	if not query: return response, 'tvshows'
	while response['page'] <= pages_max:
		params = {'query': query, 'page': page}
		result = TMDB.Search().tv(**params)
		response['results'].extend(result['results'])
		if result['page'] == result['total_pages']: break
		response['page'] = page = result['page'] + 1
	return response, 'tvshows'


def OLD_SEARCH_MOVIES(page):
	import xbmcgui

	pages_max = addon.get_setting('tmdb_pages')
	response = {'page':page, 'total_pages': page, 'results': []}
	query = xbmcgui.Dialog().input('Movies Search')
	if not query: return response, 'movies'
	while response['page'] <= pages_max:
		params = {'query': query, 'page': page}
		result = TMDB.Search().movie(**params)
		response['results'].extend(result['results'])
		if result['page'] == result['total_pages']: break
		response['page'] = page = result['page'] + 1
	return response, 'movies'


def search_tv(page, query=None):
	params = {'query': query, 'page': page}
	response = TMDB.Search().tv(**params)
	return response, 'tvshows'


def search_movies(page, query=None):
	params = {'query': query, 'page': page}
	response = TMDB.Search().movie(**params)
	return response, 'movies'
