from datetime import datetime

from resources.external.simpleplugin import Plugin
from resources.lib import common
from resources.lib import metadata, tmdb

import xbmcgui


plugin = Plugin()
current_date = datetime.now().strftime('%Y-%m-%d')
res = tmdb.TmdbImages

info_tag_dict = {
	'production_countries': 'setCountries',
	'director': 'setDirectors',
	'runtime': 'setDuration',
	'genres': 'setGenres',
	'imdb_id': 'setIMDBNumber',
	'media_type': 'setMediaType',
	'mpaa': 'setMpaa',
	'original_title': 'setOriginalTitle',
	'playcount': 'setPlaycount',
	'overview': 'setPlot',
	'release_date': 'setPremiered',
	'production_companies': 'setStudios',
	'tagline': 'setTagLine',
	'tag': 'setTags',
	'title': 'setTitle',
	'trailer': 'setTrailer',
	'vote_average': 'setRating',
	'vote_count': 'setVotes',
	'writer': 'setWriters',
	'year': 'setYear',
	# tvshow exclusive
	'episode_number': 'setEpisode',
	'season_number': 'setSeason',
	'episode_run_time': 'setDuration',
	'first_air_date': 'setPremiered',
	'air_date': 'setPremiered',
#	'networks': 'setStudios',
	'name': 'setTitle',
	'tvshowtitle': 'setTvShowTitle',
	'status': 'setTvShowStatus'
}


def info_tagger(item, meta):
	unique_ids = {i[:4]: str(val) for i in ('imdb_id', 'tmdb_id', 'tvdb_id') if (val := meta.get(i))}
	info_tag = item.getVideoInfoTag()
	info_tag.setUniqueIDs(unique_ids)
	info_tag.setCast([common.Actor(**actor) for actor in meta['credits']])
	for key in info_tag_dict:
		if key not in meta or not (arg := meta[key]): continue
		func = getattr(info_tag, info_tag_dict[key])
		func(arg)


class TvMovieObj:
	def __init__(self, m_id, mt):
		self.tmdb = m_id
		self.mt = mt
		self._meta = None
		self.list_items_gen = self.tv_worker if mt == 'tvshows' else self.movies_worker
		self.list_item = None

	@property
	def meta(self):
		if self._meta: return self._meta
		func = metadata.tv_meta if self.mt == 'tvshows' else metadata.movie_meta
		data = self._meta = func(self.tmdb)
		data['backdrop_path'] = res(data['backdrop_path']).fanart_url
		data['poster_path'] = res(data['poster_path']).poster_url
		data['logo_path'] = res(data['logo_path']).logo_url
		for i in data['credits']: i['thumbnail'] = res(i['thumbnail']).logo_url
		return data

	def tv_worker(self):
		try:
			cm = []
			meta = self.meta
			unaired = meta.get('first_air_date')
			unaired = True if not unaired else unaired > current_date
			if unaired: meta['name'] = common.UNAIRED_COLOR % meta['name']
			favs = plugin.get_url(
				action='fav_manager', media=meta['media_type'], tmdb_id=self.tmdb, title=meta['tvshowtitle'])
			cm.append((common.context['favs'], f"RunPlugin({favs})"))
			list_item = xbmcgui.ListItem()
			list_item.addContextMenuItems(cm)
			list_item.setArt({
				'poster': meta['poster_path'],
				'fanart': meta['backdrop_path'],
				'clearlogo': meta['logo_path']})
			info_tagger(list_item, meta)
			url = plugin.get_url(action='episodes_list', tmdb_id=meta['tmdb_id'])
			self.list_item = url, list_item, True
#		except Exception as e: common.logger((self.meta, type(e), e, self.tmdb))
		except: pass

	def movies_worker(self):
		try:
			cm = []
			meta = self.meta
			unaired = meta.get('release_date')
			unaired = True if not unaired else unaired > current_date
			if unaired: meta['title'] = common.UNAIRED_COLOR % meta['title']
			favs = plugin.get_url(
				action='fav_manager', media=meta['media_type'], tmdb_id=self.tmdb, title=meta['title'])
			cm.append((common.context['favs'], f"RunPlugin({favs})"))
			list_item = xbmcgui.ListItem()
			list_item.addContextMenuItems(cm)
			list_item.setArt({
				'poster': meta['poster_path'],
				'fanart': meta['backdrop_path'],
				'clearlogo': meta['logo_path']})
			info_tagger(list_item, meta)
			# list_item.setProperty('IsPlayable', 'true')
			# url = plugin.get_url(action='play', video=meta.get('url'))
			url = plugin.get_url(action='media_info')
			self.list_item = url, list_item, False
#		except Exception as e: common.logger((self.meta, type(e), e))
		except: pass


class EpisodeObj:
	def __init__(self, m_id, sn=None, en=None, show_meta=None, sn_data=None, ep_data=None):
		self.tmdb = m_id
		self.sn = sn
		self.en = en
		self._show_meta = show_meta
		self.sn_data = sn_data
		self.ep_data = ep_data
		self.list_item = []

	@property
	def list_items_gen(self):
		return self.ep_worker if self.ep_data or self.sn else self.sn_worker

	@property
	def show_meta(self):
		if self._show_meta: return self._show_meta
		meta = self._show_meta = metadata.tv_meta(self.tmdb)
		meta['backdrop_path'] = res(meta['backdrop_path']).fanart_url
		meta['poster_path'] = res(meta['poster_path']).poster_url
		meta['logo_path'] = res(meta['logo_path']).logo_url
		for i in meta['credits']: i['thumbnail'] = res(i['thumbnail']).logo_url
		return meta

	def ep_worker(self):
		meta = self.show_meta
		episodes_data = self.ep_data or metadata.season_meta(self.tmdb, self.sn)['episodes']
		if self.en: episodes_data = [ep for ep in episodes_data if ep['episode_number'] == self.en]
		for ep in episodes_data:
			try:
				_meta = meta.copy()
				_meta.update(ep)
				_meta['still_path'] = res(_meta.get('still_path')).fanart_url
				_meta['media_type'] = 'episode'
				unaired = _meta.get('air_date')
				unaired = True if not unaired else unaired > current_date
				if unaired: _meta['name'] = common.UNAIRED_COLOR % _meta['name']
				list_item = xbmcgui.ListItem()
				list_item.setArt({
					'thumb': _meta['still_path'],
					'poster': _meta['poster_path'],
					'fanart': _meta['backdrop_path'],
					'clearlogo': _meta['logo_path']})
				info_tagger(list_item, _meta)
				url = plugin.get_url(action='media_info')
				self.list_item.append((url, list_item, False))
#			except Exception as e: common.logger((_meta, type(e), e))
			except: pass

	def sn_worker(self):
		meta = self.show_meta
		seasons_data = self.sn_data or meta['seasons']
		for sn in seasons_data:
			try:
				_meta = meta.copy()
				_meta.update(sn)
				_meta['poster_path'] = res(_meta['poster_path']).poster_url
				_meta['media_type'] = 'season'
				unaired = _meta.get('air_date')
				unaired = True if not unaired else unaired > current_date
				if unaired: _meta['name'] = common.UNAIRED_COLOR % _meta['name']
				list_item = xbmcgui.ListItem()
				list_item.setArt({
					'poster': _meta.get('poster_path') or meta['poster_path'],
					'fanart': _meta['backdrop_path'],
					'clearlogo': _meta['logo_path']})
				info_tagger(list_item, _meta)
				url = plugin.get_url(
					action='episodes_list',
					tmdb_id=_meta['tmdb_id'],
					season_number=_meta['season_number'])
				self.list_item.append((url, list_item, True))
#			except Exception as e: common.logger((_meta, type(e), e))
			except: pass
