from resources.external.simpleplugin import Addon, Plugin
from resources.lib import common


addon, plugin = Addon(), Plugin()


class Example:
	__slots__  = ['MENU']

	def __init__(self, params):
		self.MENU = {'root': root, 'tele': tele, 'movies': movies, 'tools': tools}
		mode = params.get('mode', 'main')
		func = getattr(self, mode, self.main)
		func(params)

	def main(self, params):
		def _worker(items):
			for item in items:
				cm = []
				poster = item.get('icon', 'DefaultFolder.png')
				is_folder = item.get('is_folder', True)
				if 'list_id' in item:
					favs = plugin.get_url(action='fav_manager', media='list', list_id=item['list_id'], title=item['name'])
					cm.append((common.context['favs'], f"RunPlugin({favs})"))
				# URL: plugin://plugin.video.foo/?action=subfolder
				url = plugin.get_url(**item)
				list_item = container.make_listitem()
				list_item.addContextMenuItems(cm)
				list_item.setArt({'icon': poster, 'poster': poster})
				info_tag = list_item.getVideoInfoTag()
				info_tag.setMediaType('video')
				info_tag.setTitle(item['name'])
				yield (url, list_item, is_folder)

		container = common.Container()
		mode = params.get('mode', 'root')
		items = self.MENU[mode]
		container.item_list = list(_worker(items))
		container.category = params.get('name')
		container.end()

	def favorites(self, params):
		from resources.lib import favorites
		lists = favorites.fav_lists()
		items = [
			{'action': 'favorites', 'mode': 'tvshow', 'name': 'Favorite Shows', 'icon': 'DefaultTVShows.png'},
			{'action': 'favorites', 'mode': 'movie', 'name': 'Favorite Movies', 'icon': 'DefaultMovies.png'}]
		for media, list_id, name in lists:
			items.append({'action': 'trakt_lists_items', 'list_id': list_id, 'name': name})
		self.MENU['favorites'] = items
		self.main({'mode': 'favorites', 'name': params.get('name')})

	def trakt(self, params):
		if addon.get_setting('trakt_token'):
			items = [
				{'action': 'trakt_lists', 'mode': 'personal_lists', 'name': 'Trakt Personal Lists', 'icon': 'DefaultVideoPlaylists.png'},
				{'action': 'trakt_lists_items', 'mode': 'watchlist', 'name': 'Trakt Watchlist', 'icon': 'DefaultVideoPlaylists.png'},
				{'action': 'trakt_lists_items', 'mode': 'history', 'name': 'Trakt History', 'icon': 'DefaultVideoPlaylists.png'},
				{'action': 'trakt_account_stats', 'is_folder': False, 'name': 'Trakt Account Stats', 'icon': 'DefaultAddonService.png'},
				{'action': 'trakt_revoke', 'is_folder': False, 'name': 'Trakt Revoke', 'icon': 'DefaultAddonService.png'}]
		else:
			items = [
				{'action': 'trakt_authorize', 'is_folder': False, 'name': 'Trakt Authorize', 'icon': 'DefaultAddonService.png'}]
		self.MENU['trakt'] = items
		self.main({'mode': 'trakt', 'name': params.get('name')})


root = [
	{'action': 'root', 'mode': 'tele', 'name': 'TV', 'icon': 'DefaultTVShows.png'},
	{'action': 'root', 'mode': 'movies', 'name': 'Movies', 'icon': 'DefaultMovies.png'},
	{'action': 'root', 'mode': 'favorites', 'name': 'Favorites'},
	{'action': 'trakt_lists', 'mode': 'lists_trending', 'name': 'Trakt Trending Lists', 'icon': 'DefaultVideoPlaylists.png'},
	{'action': 'trakt_lists', 'mode': 'lists_popular', 'name': 'Trakt Popular Lists', 'icon': 'DefaultVideoPlaylists.png'},
	{'action': 'trakt_lists', 'mode': 'lists_search', 'name': 'Search Trakt Lists', 'icon': 'DefaultVideoPlaylists.png'},
	{'action': 'root', 'mode': 'trakt', 'name': 'Trakt Account'},
	{'action': 'root', 'mode': 'tools', 'name': 'Tools'}
]

tele = [
	{'action': 'tv_movies_lists', 'mode': 'trakt_shows_trending', 'name': 'Trakt Trending TV', 'icon': 'DefaultTVShows.png'},
	{'action': 'tv_movies_lists', 'mode': 'trakt_shows_watched', 'name': 'Trakt Most Watched TV', 'icon': 'DefaultTVShows.png'},
	{'action': 'tv_movies_lists', 'mode': 'trending_tv', 'name': 'Trending TV', 'icon': 'DefaultTVShows.png'},
	{'action': 'tv_movies_lists', 'mode': 'popular_tv', 'name': 'Popular TV', 'icon': 'DefaultTVShows.png'},
	{'action': 'tv_movies_lists', 'mode': 'latest_tv', 'name': 'Latest Shows', 'icon': 'DefaultTVShows.png'},
	{'action': 'favorites', 'mode': 'tvshow', 'name': 'Favorite Shows', 'icon': 'DefaultTVShows.png'},
	{'action': 'tv_movies_lists', 'mode': 'search_tv', 'name': 'TV Search', 'icon': 'DefaultTVShows.png'},
	{'action': 'trakt_lists_items', 'mode': 'watchlist_tv', 'name': 'Trakt Watchlist Shows', 'icon': 'DefaultTVShows.png'}
]

movies = [
	{'action': 'tv_movies_lists', 'mode': 'trakt_movies_trending', 'name': 'Trakt Trending Movies', 'icon': 'DefaultMovies.png'},
	{'action': 'tv_movies_lists', 'mode': 'trakt_movies_watched', 'name': 'Trakt Most Watched Movies', 'icon': 'DefaultMovies.png'},
	{'action': 'tv_movies_lists', 'mode': 'trending_movies', 'name': 'Trending Movies', 'icon': 'DefaultMovies.png'},
	{'action': 'tv_movies_lists', 'mode': 'popular_movies', 'name': 'Popular Movies', 'icon': 'DefaultMovies.png'},
	{'action': 'tv_movies_lists', 'mode': 'latest_digital', 'name': 'Latest Digital', 'icon': 'DefaultMovies.png'},
	{'action': 'favorites', 'mode': 'movie', 'name': 'Favorite Movies', 'icon': 'DefaultMovies.png'},
	{'action': 'tv_movies_lists', 'mode': 'search_movies', 'name': 'Movies Search', 'icon': 'DefaultMovies.png'},
	{'action': 'trakt_lists_items', 'mode': 'watchlist_movies', 'name': 'Trakt Watchlist Movies', 'icon': 'DefaultMovies.png'}
]

tools = [
#	{'action': 'test_func', 'mode': 'default', 'is_folder': False, 'name': 'test_func', 'icon': 'DefaultVideoPlaylists.png'},
#	{'action': 'test_func', 'mode': 'default', 'name': 'test_func', 'icon': 'DefaultVideoPlaylists.png'},
	{'action': 'settings_open', 'is_folder': False, 'name': 'Addon Settings', 'icon': 'DefaultAddonService.png'},
	{'action': 'cache_clear_meta', 'is_folder': False, 'name': 'Clear Meta Cache', 'icon': 'DefaultAddonService.png'},
	{'action': 'cache_clear_memory', 'is_folder': False, 'name': 'Clear Memory Cache', 'icon': 'DefaultAddonService.png'},
#	{'action': 'cache_clear', 'mode': 'main_cache', 'is_folder': False, 'name': 'Clear Main Cache', 'icon': 'DefaultAddonService.png'},
	{'action': 'changelog_txt', 'is_folder': False, 'name': 'View Changelog', 'icon': 'DefaultAddonService.png'}
]
