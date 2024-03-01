import sqlite3
import time

from resources.lib import common


PROFILE_PATH = common.profile_path()

file_name_mapping = {
	'maincache': 'cache_main.db',
	'metacache': 'cache_meta.db',
	'watched': 'watched.db',
}


class Cache: # not too good with python and sql, this probably needs improvement
	def __init__(self, table=None, file=None):
		self.path = common.joinPath(PROFILE_PATH, file_name_mapping[file])
		self.table = table or file
		self.__connect_database()
		self.__set_PRAGMAS()

	def __connect_database(self):
		self.dbcon = sqlite3.connect(self.path, timeout=60, isolation_level=None)
#		self.dbcon.row_factory = db.Row # return results indexed by field names and not numbers so we can convert to dict

	def __set_PRAGMAS(self):
		self.dbcur = self.dbcon.cursor()
		self.dbcur.execute('''PRAGMA journal_mode = OFF''')
		self.dbcur.execute('''PRAGMA synchronous = OFF''')

	def __del__(self):
		try:
			self.dbcur.close()
			self.dbcon.close()
		except: pass

	def select_single(self, query):
		try:
			self.dbcur.execute(query)
			return self.dbcur.fetchone()
		except: pass

	def select_all(self, query, parms=None):
		try:
			if parms:
				self.dbcur.execute(query, parms)
			else:
				self.dbcur.execute(query)
			return self.dbcur.fetchall()
		except: pass

	def insert(self, query, values):
		try:
			self.dbcur.execute(query, values)
			self.dbcon.commit()
		except: pass

	def get_current_time(self):
		return int(time.time())

	def clear_tables(self):
		try:
			self.dbcur.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
			tables = self.dbcur.fetchall()
			for table in tables:
				query = f"DELETE FROM {table[0]}"
				self.dbcur.execute(query)
			self.dbcur.execute('VACUUM')
		except: pass

	def clear_expired(self):
		self.current_time = self.get_current_time()
		try:
			self.dbcur.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
			tables = self.dbcur.fetchall()
			for table in tables:
				query = f"DELETE FROM {table[0]} WHERE expires < '{self.current_time}'"
				self.dbcur.execute(query)
			self.dbcur.execute('VACUUM')
		except: pass
