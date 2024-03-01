import json
#import zlib

from resources.external.simpleplugin import Plugin
from resources.lib.cache import Cache
from resources.lib.tmdb import TMDB
#from resources.lib import common


plugin = Plugin()

EXPIRES_24_HOURS = 60*24


class MetaCache(Cache): # not too good with python and sql, this probably needs improvement
	TABLES = [
		"""\
		CREATE TABLE IF NOT EXISTS metacache
		(media_type TEXT NOT NULL, tmdb_id INTEGER NOT NULL, title TEXT, meta TEXT, expires INTEGER,
		UNIQUE(tmdb_id));""",
		"""\
		CREATE TABLE IF NOT EXISTS seasons
		(media_type TEXT NOT NULL, tmdb_id INTEGER NOT NULL, season INTEGER, meta TEXT, expires INTEGER,
		UNIQUE(tmdb_id, season));"""]

	def __init__(self, table=None, file='metacache'):
		super().__init__(table, file)
		self.__create_cache_db()
		self.current_time = self.get_current_time()

	def __create_cache_db(self):
		for sql in self.TABLES: self.dbcur.execute(sql)

	def get(self, tmdb_id, season=None):
		if season:
			self.table = 'seasons'
			sql = f"SELECT * FROM {self.table} WHERE tmdb_id = '{tmdb_id}' AND season = '{season}';"
			data = self.select_single(sql)
		else:
			sql = f"SELECT * FROM {self.table} WHERE tmdb_id = '{tmdb_id}';"
			data = self.select_single(sql)
		if not data: return data
		expired = self.current_time > data[4]
		data = None if expired else json.loads(data[3])
#		data = None if expired else json.loads(zlib.decompress(data[3]).decode('utf-8'))
		return data

	def set(self, data, tmdb_id=None, season=None, expires=168):
		expires = self.current_time + expires * 3600
		if season:
			self.table = 'seasons'
			season = data['season_number']
			values = 'tvshow', tmdb_id, season, json.dumps(data), expires
			sql = f"INSERT OR REPLACE INTO {self.table} VALUES (?, ?, ?, ?, ?);"
		else:
			mt, tmdb_id = data['media_type'], data['tmdb_id']
			title = data['tvshowtitle'] if mt == 'tvshow' else data['title']
			values = mt, tmdb_id, title, json.dumps(data), expires
#			values = mt, tmdb_id, title, zlib.compress(json.dumps(data).encode('utf-8')), expires
			sql = f"INSERT OR REPLACE INTO {self.table} VALUES (?, ?, ?, ?, ?);"
		self.insert(sql, values)


@plugin.mem_cached(EXPIRES_24_HOURS)
def season_meta(tmdb_id, season):
	db = MetaCache()
	data = db.get(tmdb_id, season)
	if data: return data
	season = TMDB.TV_Seasons(tmdb_id, season)
	data = season.info()
	try: del data['_id']
	except: pass
	for i in data['episodes']:
		i['still_path'] = i['still_path'] or ''
		i['crew'] = i['guest_stars'] = '' # tmi, bloats cache
	try: db.set(data, tmdb_id, season)
	except: pass
	return data


@plugin.mem_cached(EXPIRES_24_HOURS)
def tv_meta(meta):
	excludes = ('created_by', 'external_ids', 'images', 'last_episode_to_air', 'next_episode_to_air', 'spoken_languages')
	params = {'language': 'en', 'append_to_response': 'credits,external_ids,images'}
	tmdb_id = meta['id'] if isinstance(meta, dict) else meta
	db = MetaCache()
	data = db.get(tmdb_id)
	if data: return data
	try:
		data = {}
		show = TMDB.TV(tmdb_id)
		response = show.info(**params)
		data.update(response)
		try: year = int(data['first_air_date'][:4])
		except: year = 0
		data.update({'tmdb_id': tmdb_id, 'tvshowtitle': data['name'], 'year': year, 'media_type': 'tvshow'})
		data['episode_run_time'] = data['episode_run_time'][0] if data['episode_run_time'] else 0
		data['genres'] = [i['name'] for i in data['genres']]
		data['networks'] = [i['name'] for i in data['networks']]
		data['production_companies'] = [i['name'] for i in data['production_companies']]
		data['production_countries'] = [i['iso_3166_1'] for i in data['production_countries']]
		if 'imdb_id' in data['external_ids']: data['imdb_id'] = data['external_ids']['imdb_id']
		try:
			credits = [
				{'name': i['name'], 'role': i['character'], 'order': i['order'],
				 'thumbnail': i['profile_path'] or ''}
				for i in data['credits']['cast']]
		except: credits = []
		data['credits'] = credits
		try:
			logo_path = [i['file_path'] for i in data['images']['logos']
				if 'file_path' in i if i['file_path'].endswith('png')][0]
			logo_path = logo_path or ''
		except: logo_path = ''
		data['logo_path'] = logo_path
		for i in data:
			if i in excludes or data[i] is None:
				data[i] = ''
		try: db.set(data)
		except: pass
	except: pass
	return data


@plugin.mem_cached(EXPIRES_24_HOURS)
def movie_meta(meta):
	excludes = ('external_ids', 'images', 'spoken_languages', 'video')
	params = {'language': 'en', 'append_to_response': 'credits,external_ids,images'}
	tmdb_id = meta['id'] if isinstance(meta, dict) else meta
	db = MetaCache()
	data = db.get(tmdb_id)
	if data: return data
	try:
		data = {}
		movie = TMDB.Movies(tmdb_id)
		response = movie.info(**params)
		data.update(response)
		try: year = int(data['release_date'][:4])
		except: year = 0
		data.update({'tmdb_id': tmdb_id, 'year': year, 'media_type': 'movie'})
		data['genres'] = [i['name'] for i in data['genres']]
		data['production_companies'] = [i['name'] for i in data['production_companies']]
		data['production_countries'] = [i['iso_3166_1'] for i in data['production_countries']]
		if 'imdb_id' in data['external_ids']: data['imdb_id'] = data['external_ids']['imdb_id']
		try:
			credits = [
				{'name': i['name'], 'role': i['character'], 'order': i['order'],
				 'thumbnail': i['profile_path'] or ''}
				for i in data['credits']['cast']]
		except: credits = []
		data['credits'] = credits
		try:
			logo_path = [
				i['file_path'] for i in data['images']['logos']
				if 'file_path' in i if i['file_path'].endswith('png')][0]
			logo_path = logo_path or ''
		except: logo_path = ''
		data['logo_path'] = logo_path
		for i in data:
			if i in excludes or data[i] is None:
				data[i] = ''
		try: db.set(data)
		except: pass
	except: pass
	return data
