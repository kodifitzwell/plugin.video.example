from resources.external.simpleplugin import Addon, Plugin
from resources.lib import common
from resources.lib import tmdb, trakt
from resources.lib.objects import TvMovieObj, EpisodeObj


addon, plugin = Addon(), Plugin()
Container, Gui = common.Container, common.Gui


class TvMoviesList(Container, Gui):
	def run(self, params):
		mode = params['mode']
		page = params.get('page', 1)
		if   mode.startswith('trakt'):
			response, content = getattr(trakt, mode)(page)
			mt = 'show' if content == 'tvshows' else 'movie'
			response['results'] = [
				{'id': i[mt]['ids']['tmdb']} for i in response['results']]
		elif 'search' in mode:
			query = params.get('query')
			if not query: query = params['query'] = self.input(params['name'])
			response, content = getattr(tmdb, mode)(page, query)
		else: response, content = getattr(tmdb, mode)(page)
		with self.Pool(self.threads) as pool:
			items = []
			for i in response['results']:
				items.append(i := TvMovieObj(i['id'], content))
				pool.submit(i.list_items_gen)
		self.item_list = [i.list_item for i in items if i.list_item]
		if response['page'] < response['total_pages']:
			params['page'] = response['page'] + 1
			url = plugin.get_url(**params)
			dir_item = self.make_listitem(label=f"NEXT PAGE ({params['page']})")
			self.item_list.append((url, dir_item, True))
		self.category = params.get('name')
		self.content = content
		self.end()


class EpisodesList(Container):
	def run(self, params):
		content = 'episodes'
		tmdb_id = int(params['tmdb_id'])
		show = EpisodeObj(tmdb_id)
		if addon.get_setting('filter_seasons'):
			seasons = show.show_meta['seasons'] = [
				sn for sn in show.show_meta['seasons'] if sn['season_number'] > 0]
		else: seasons = show.show_meta['seasons']
		if 'season_number' in params or len(seasons) < 2:
			show.sn = int(params.get('season_number', 1))
			show.list_items_gen()
			self.item_list = show.list_item if show.list_item else []
		elif addon.get_setting('flatten_seasons'):
			items = []
			self.threads = len(seasons) + 1
			with self.Pool(self.threads) as pool:
				for i in seasons:
					i = EpisodeObj(tmdb_id, i['season_number'], show_meta=show.show_meta)
					items.append(i)
					pool.submit(i.list_items_gen)
			self.item_list = [lis for i in items for lis in i.list_item if i.list_item]
		else:
			content = 'seasons'
			show.list_items_gen()
			self.item_list = show.list_item if show.list_item else []
		self.category = show.show_meta.get('tvshowtitle')
		self.content = content
		self.end()


class TraktLists(Container, Gui):
	def run(self, params):
		mode = params['mode']
		page = params.get('page', 1)
		if mode == 'lists_search':
			query = params.get('query')
			if not query: query = params['query'] = self.input(params['name'])
			response = trakt.lists_search(page, query)
		else: response = getattr(trakt, mode)(page)
		self.item_list = list(self.trakt_lists_worker(response['results']))
		if response['page'] < response['total_pages']:
			params['page'] = response['page'] + 1
			url = plugin.get_url(**params)
			dir_item = self.make_listitem(label=f"NEXT PAGE ({params['page']})")
			self.item_list.append((url, dir_item, True))
		self.category = params.get('name')
		self.end()

	def trakt_lists_worker(self, meta_list):
		for i in meta_list:
			try:
				cm = []
				if 'list' in i: i = i['list']
#				if i['privacy'] != 'public': continue
				l_id = i['ids']['trakt']
				name = i['name']
				desc = i['description']
				link = i['share_link']
				like = i['likes']
				user = i['user']['username']
				count = i['item_count']
				label = f"[B]{name}[/B] | ({count}) - [I]{user}[/I]"
				title = f"[B]{name}[/B] | [I]{user}[/I]"
				plot = f"Likes: {like}\n\n{link}\n\n{desc}"
				favs = plugin.get_url(action='fav_manager', media='list', list_id=l_id, title=title)
				cm.append((common.context['favs'], f"RunPlugin({favs})"))
				list_item = self.make_listitem(label=label)
				list_item.addContextMenuItems(cm)
				info_tag = list_item.getVideoInfoTag()
				info_tag.setMediaType('video')
				info_tag.setPlot(plot)
				url = plugin.get_url(action='trakt_lists_items', list_id=l_id, name=name)
				yield (url, list_item, True)
#			except Exception as e: common.logger((i, type(e), e))
			except: pass


class TraktItems(Container, Gui):
	def run_protected(self, params):
		if addon.get_setting('trakt_token'): return self.run(params)
		self.notify_fail('Trakt account not found')
		self.category = params.get('name')
		self.end()

	def run(self, params):
		page = params.get('page', 1)
		mode = params.get('mode')
		limit = trakt.PAGE_LIMIT
		if   mode == 'history':
			response = trakt.Account().history(page=page, limit=limit, extended='full')
		elif mode == 'watchlist':
			response = trakt.Account().watchlist(page=page, limit=limit, extended='full')
		elif mode == 'watchlist_tv':
			response = trakt.Account().watchlist(page=page, limit=limit, extended='full', type='shows')
		elif mode == 'watchlist_movies':
			response = trakt.Account().watchlist(page=page, limit=limit, extended='full', type='movies')
		else:
			list_id = params['list_id']
			response = trakt.lists_items(list_id, page)
		counter = dict.fromkeys(('movies', 'tvshows', 'seasons', 'episodes'), 0)
		items = list(trakt_items_to_objs(response['results'], counter))
		content, val = max(counter.items(), key=lambda k: k[1])
		with self.Pool(limit + 1) as pool:
			for i in items: pool.submit(i['item'].list_items_gen)
		for i in items:
			if not (item := i['item'].list_item): continue
			if i['media_type'] in ('season', 'episode'): self.item_list.extend(item)
			else: self.item_list.append(item)
		if response['page'] < response['total_pages']:
			params['page'] = response['page'] + 1
			url = plugin.get_url(**params)
			dir_item = self.make_listitem(label=f"NEXT PAGE ({params['page']})")
			self.item_list.append((url, dir_item, True))
		self.category = params.get('name')
		self.content = content
		self.unsorted = True
		self.end()


def trakt_items_to_objs(items, count):
	for i in items:
		try:
			if (mt := i['type']) not in ('movie' , 'show', 'season', 'episode'): continue
			if mt == 'movie':
				count['movies'] += 1
				m_id, media = i['movie']['ids']['tmdb'], 'movies'
			else:
				if mt == 'show': count['tvshows'] += 1
				m_id, media = i['show']['ids']['tmdb'], 'tvshows'
			if not m_id: raise ValueError
			data = {'media_type': media, 'item': TvMovieObj(m_id, media)}
			# instead of calling tvshow meta and season meta (two api calls per item),
			# build minimal season/episode meta from trakt extended info. the art and other
			# info will be filled in from tvshow meta (one api call per item) by worker func.
			if mt == 'season':
				count['seasons'] += 1
				data['media_type'] = 'season'
				sn_data = data['seasons'] = [{
					'season_number': i[mt]['number'],
					'air_date': i[mt]['first_aired'][:10] if i[mt]['first_aired'] else '',
					'overview': i[mt]['overview'] or i['show']['overview'],
					'name': f"{i['show']['title']}: {i[mt]['title']}",
					'vote_average': i[mt]['rating'],
					'vote_count': i[mt]['votes']}]
				data['item'] = EpisodeObj(m_id, sn_data=sn_data)
			if mt == 'episode':
				count['episodes'] += 1
				data['media_type'] = 'episode'
				ep_data = data['episodes'] = [{
					'episode_number': i[mt]['number'],
					'runtime': i[mt]['runtime'],
					'season_number': i[mt]['season'],
					'air_date': i[mt]['first_aired'][:10] if i[mt]['first_aired'] else '',
					'overview': i[mt]['overview'] or i['show']['overview'],
					'name': f"{i['show']['title']}: {i[mt]['season']}x{i[mt]['number']:02d}. {i[mt]['title']}",
					'vote_average': i[mt]['rating'],
					'vote_count': i[mt]['votes']}]
				data['item'] = EpisodeObj(m_id, ep_data=ep_data)
			yield data
#		except Exception as e: common.logger((i, type(e), e))
		except: pass
