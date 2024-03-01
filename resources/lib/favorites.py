from resources.lib import common
from resources.lib.cache import Cache
from resources.lib.objects import TvMovieObj


Container = common.Container


class Favorites(Cache): # not too good with python and sql, this probably needs improvement
	TABLES = [
		"""\
		CREATE TABLE IF NOT EXISTS favorites
		(media_type TEXT NOT NULL, tmdb_id INTEGER NOT NULL, title TEXT,
		UNIQUE(media_type, tmdb_id));"""]

	def __init__(self, table='favorites', file='watched'):
		super().__init__(table, file)
		self.__create_cache_db()
		self.current_time = self.get_current_time()

	def __create_cache_db(self):
		for sql in self.TABLES: self.dbcur.execute(sql)

	def get(self, tmdb_id):
		sql = f"SELECT * FROM {self.table} WHERE tmdb_id = '{tmdb_id}';"
		data = self.select_single(sql)
		return data

	def get_media(self, media):
		sql = f"SELECT * FROM {self.table} WHERE media_type = '{media}';"
		data = self.select_all(sql)
		return data

	def set(self, media, tmdb_id, title):
		values = media, tmdb_id, title
		sql = f"INSERT OR REPLACE INTO {self.table} VALUES (?, ?, ?);"
		self.insert(sql, values)

	def remove(self, media, tmdb_id):
		values = media, tmdb_id
		sql = f"DELETE FROM {self.table} WHERE media_type = ? and tmdb_id = ?;"
		self.insert(sql, values)

	def clear_tables(self):
		try:
			query = f"DELETE FROM {self.table}"
			self.dbcur.execute(query)
			self.dbcur.execute('VACUUM')
		except: pass


class Fav(Container):
	def run(self, params):
		mode = params['mode']
		db = Favorites()
		data = db.get_media(mode)
		results = [{'id': i[1]} for i in data]
		response = {'results': results, 'page': 1 , 'total_pages': 1}
		content = 'tvshows' if mode == 'tvshow' else 'movies'
		with self.Pool(self.threads) as pool:
			items = []
			for i in response['results']:
				items.append(i := TvMovieObj(i['id'], content))
				pool.submit(i.list_items_gen)
		self.item_list = [i.list_item for i in items if i.list_item]
		self.category = params.get('name')
		self.content = content
		self.end()


def fav_lists():
	db = Favorites()
	data = db.get_media('list')
	return data
