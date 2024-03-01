import requests
from requests.adapters import HTTPAdapter

from resources.external.simpleplugin import Addon, Plugin
#from resources.lib import common


addon, plugin = Addon(), Plugin()

session = requests.Session()
session.mount('https://api.trakt.tv', HTTPAdapter(pool_maxsize=100))

EXPIRES_24_HOURS = 60*24
PAGE_LIMIT = 50
REQUESTS_SESSION = session
REQUESTS_TIMEOUT = (2.05, 4.05)
#CLIENT_ID = ''
#CLIENT_SECRET = ''

prop = addon.get_mem_storage(addon.name)
try: CLIENT_ID = prop['trakt_client']
except: CLIENT_ID = prop['trakt_client'] = addon.get_setting('trakt_client')
try: TRAKT_TOKEN = prop['trakt_token']
except: TRAKT_TOKEN = prop['trakt_token'] = addon.get_setting('trakt_token')


class Trakt:
	headers = {'Content-Type': 'application/json',
			   'trakt-api-version': '2',
			   'trakt-api-key': f"{CLIENT_ID}",
			   'Connection': 'close'}
	BASE_PATH = ''
	URLS = {}

	def __init__(self):
		self.base_uri = 'https://api.trakt.tv'
		self.session = REQUESTS_SESSION
		self.timeout = REQUESTS_TIMEOUT

	def _get_path(self, key):
		return self.BASE_PATH + self.URLS[key]

	def _get_complete_url(self, path):
		return '{base_uri}/{path}'.format(base_uri=self.base_uri, path=path)

	def _request(self, method, path, params=None, payload=None):
		url = self._get_complete_url(path)
		response = self.session.request(
			method,
			url,
			params=params,
			json=payload if payload else payload,
			headers=self.headers, timeout=self.timeout)
		response.raise_for_status()
		response.encoding = 'utf-8'
		results = response.json()
		if 'x-sort-by' and 'x-sort-how' in response.headers:
			key, how = response.headers['x-sort-by'], response.headers['x-sort-how']
			reverse = how != 'asc'
			if key == 'added': results.sort(key=lambda x: x['listed_at'], reverse=reverse)
		if 'x-pagination-page' and 'x-pagination-page-count' in response.headers:
			page = int(response.headers['x-pagination-page'])
			total_pages = int(response.headers['x-pagination-page-count'])
			return {'results': results, 'page': page, 'total_pages': total_pages}
		return results

	def _GET(self, path, params=None):
		return self._request('GET', path, params=params)

	def _POST(self, path, params=None, payload=None):
		return self._request('POST', path, params=params, payload=payload)

	def _PUT(self, path, params=None, payload=None):
		return self._request('PUT', path, params=params, payload=payload)

	def _DELETE(self, path, params=None, payload=None):
		return self._request('DELETE', path, params=params, payload=payload)


class List(Trakt): # class for methods that do not require authorization header
	BASE_PATH = '{media}'
	URLS = {
		'trending': '/trending',
		'popular': '/popular',
		'watched': '/watched/{period}',
		'search': '/search/{type}',
		'items': '/{list_id}/items'
	}

	def __init__(self, media=''):
		super().__init__()
		self.media = media

	def trending(self, **kwargs):
		path = self._get_path('trending').format(media=self.media)

		response = self._GET(path, kwargs)
		return response

	def popular(self, **kwargs):
		path = self._get_path('popular').format(media=self.media)

		response = self._GET(path, kwargs)
		return response

	def watched(self, period='week', **kwargs):
		path = self._get_path('watched').format(media=self.media, period=period)

		response = self._GET(path, kwargs)
		return response

	def search(self, type='list', **kwargs):
		path = self._get_path('search').format(media=self.media, type=type)

		response = self._GET(path, kwargs)
		return response

	def items(self, list_id='', **kwargs):
		path = self._get_path('items').format(media=self.media, list_id=list_id)

		response = self._GET(path, kwargs)
		return response


@plugin.mem_cached(EXPIRES_24_HOURS)
def trakt_shows_trending(page):
	params = {'page': page, 'limit': 20}
	response = List('shows').trending(**params)
	return response, 'tvshows'


@plugin.mem_cached(EXPIRES_24_HOURS)
def trakt_shows_watched(page):
	params = {'page': page, 'limit': 20}
	response = List('shows').watched(**params)
	return response, 'tvshows'


@plugin.mem_cached(EXPIRES_24_HOURS)
def trakt_movies_trending(page):
	params = {'page': page, 'limit': 20}
	response = List('movies').trending(**params)
	return response, 'movies'


@plugin.mem_cached(EXPIRES_24_HOURS)
def trakt_movies_watched(page):
	params = {'page': page, 'limit': 20}
	response = List('movies').watched(**params)
	return response, 'movies'


@plugin.mem_cached(EXPIRES_24_HOURS)
def lists_trending(page):
	params = {'page': page, 'limit': PAGE_LIMIT}
	response = List('lists').trending(**params)
	return response


@plugin.mem_cached(EXPIRES_24_HOURS)
def lists_popular(page):
	params = {'page': page, 'limit': PAGE_LIMIT}
	response = List('lists').popular(**params)
	return response


@plugin.mem_cached(EXPIRES_24_HOURS)
def lists_items(list_id, page):
	# if the response is paginated, the order does not match the web page, seems illogical.
	# would seem more logical if trakt paginated as list pref instead of always rank
	# unfortunate to have to pull the full list and paginate manually.
	# params = {'list_id': list_id, 'page': page, 'limit': PAGE_LIMIT, 'extended': 'full'}
	params = {'list_id': list_id, 'extended': 'full'}
	response = List('lists').items(**params)
	if (limit := PAGE_LIMIT): # paginate results manually
		results = response['results']
		results = [results[i:i + limit] for i in range(0, len(results), limit)]
		response['page'], response['total_pages'] = int(page), len(results)
		response['results'] = results[response['page'] - 1]
	return response


def OLD_LISTS_SEARCH(page):
	import xbmcgui

	pages_max = addon.get_setting('tmdb_pages')
	response = {'page': page, 'total_pages': page, 'results': []}
	query = xbmcgui.Dialog().input('Search Lists')
	if not query: return response, 'files'
	while response['page'] <= pages_max:
		params = {'query': query, 'page': page, 'limit': 20}
		result = List().search(**params)
		response['results'].extend(result['results'])
		if result['page'] == result['total_pages']: break
		response['page'] = page = result['page'] + 1
	return response, 'files'


def lists_search(page, query=''):
	params = {'query': query, 'page': page, 'limit': PAGE_LIMIT}
	response = List().search(**params)
	return response


class Account(Trakt): # add methods to this class for paths that require authorization header
	BASE_PATH = ''
	URLS = {
		'code': 'oauth/device/code',
		'token': 'oauth/device/token',
		'revoke': 'oauth/revoke',
		'refresh': 'oauth/token',
		'me': 'users/me',
		'settings': 'users/settings',
		'stats': 'users/{id}/stats',
		'lists': 'users/{id}/lists',
		'history': 'users/{id}/history/{type}',
		'watchlist': 'users/{id}/watchlist/{type}{sort}',
		'collection': 'users/{id}/collection/{type}'
	}

	def _request(self, method, path, params=None, payload=None):
		url = self._get_complete_url(path)
		if TRAKT_TOKEN: self.headers['Authorization'] = f"Bearer {TRAKT_TOKEN}"

		response = self.session.request(
			method,
			url,
			params=params,
			json=payload if payload else payload,
			headers=self.headers, timeout=self.timeout)

		if   response.status_code == 400: # Pending - waiting for the user to authorize your app
			return None
		if   response.status_code == 403: # Forbidden - invalid API key or unapproved app
			trakt_refresh()
			response = self._request(method, path, params=params, payload=payload)
		elif response.status_code == 429: # Rate Limit Exceeded
			"""
			import xbmc
			retry = respose.headers.get('retry-after', 10)
			xbmc.sleep(retry * 1000)
			response = self._request(method, path, params=params, payload=payload)
			"""
			...

		response.raise_for_status()
		response.encoding = 'utf-8'
		results = response.json()
		if 'x-sort-by' and 'x-sort-how' in response.headers:
			key, how = response.headers['x-sort-by'], response.headers['x-sort-how']
			reverse = how != 'asc'
			if key == 'added': results.sort(key=lambda x: x['listed_at'], reverse=reverse)
		if 'x-pagination-page' and 'x-pagination-page-count' in response.headers:
			page = int(response.headers['x-pagination-page'])
			total_pages = int(response.headers['x-pagination-page-count'])
			return {'results': results, 'page': page, 'total_pages': total_pages}
		return results

	def _get_device_code(self):
		path = self._get_path('code')

		payload = {
			'client_id': CLIENT_ID
		}

		response = self._POST(path, payload=payload)
		return response

	def _get_device_token(self, code=None):
		path = self._get_path('token')
		url = self._get_complete_url(path)
		secret = addon.get_setting('trakt_secret')

		payload = {
			'code': code,
			'client_id': CLIENT_ID,
			'client_secret': secret
		}

		response = self._POST(path, payload=payload)
		return response

	def revoke_authorization(self):
		path = self._get_path('revoke')
		secret = addon.get_setting('trakt_secret')

		payload = {
			'token': TRAKT_TOKEN,
			'client_id': CLIENT_ID,
			'client_secret': secret
		}

		response = self._POST(path, payload=payload)
		return response

	def refresh_authorization(self):
		path = self._get_path('refresh')
		secret = addon.get_setting('trakt_secret')
		refresh = addon.get_setting('trakt_refresh')

		payload = {
			'refresh_token': refresh,
			'client_id': CLIENT_ID,
			'client_secret': secret,
			'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
			'grant_type': 'refresh_token'
		}

		response = self._POST(path, payload)
		return response

	def whoami(self):
		path = self._get_path('me')

		response = self._GET(path)
		return response

	def settings(self):
		path = self._get_path('settings')

		response = self._GET(path)
		return response

	def stats(self, id=''):
		path = self._get_path('stats').format(id=id)

		response = self._GET(path)
		return response

	def lists(self, id=''):
		if not id: id = self.whoami()['ids']['slug']
		path = self._get_path('lists').format(id=id)

		response = self._GET(path)
		return response

	def history(self, id='', type='', **kwargs):
		if not id: id = self.whoami()['ids']['slug']
		path = self._get_path('history').format(id=id, type=type)

		response = self._GET(path, kwargs)
		return response

	def watchlist(self, id='', type='', sort='', **kwargs):
		if not id: id = self.whoami()['ids']['slug']
		if type and sort: sort = f"/{sort}"
		path = self._get_path('watchlist').format(id=id, type=type, sort=sort)

		response = self._GET(path, kwargs)
		return response

	def collection(self, id='', type=''):
		if not id: id = self.whoami()['ids']['slug']
		path = self._get_path('collection').format(id=id, type=type)

		response = self._GET(path)
		return response


def trakt_refresh(params):
	import time

	response = Account().refresh_authorization()
	addon.set_setting('trakt.token', response['access_token'])
	addon.set_setting('trakt.refresh', response['refresh_token'])
	addon.set_setting('trakt.expires', int(time.time() + 7776000))
	TRAKT_TOKEN = prop['trakt_token'] = addon.get_setting('trakt_token')


def personal_lists(page):
	results = Account().lists()
	response = {'results': results, 'page': page, 'total_pages': page}
	return response
