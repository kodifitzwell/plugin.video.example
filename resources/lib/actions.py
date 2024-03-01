from resources.external.simpleplugin import Addon, Plugin
#from resources.lib import common


addon, plugin = Addon(), Plugin()


@plugin.action()
def tv_movies_lists(params):
	from resources.lib import lists
	lists.TvMoviesList().run(params)


@plugin.action()
def episodes_list(params):
	from resources.lib import lists
	lists.EpisodesList().run(params)


@plugin.action()
def trakt_lists(params):
	from resources.lib import lists
	lists.TraktLists().run(params)


@plugin.action()
def trakt_lists_items(params):
	from resources.lib import lists
	mode = params.get('mode')
	if mode: lists.TraktItems().run_protected(params)
	else: lists.TraktItems().run(params)


@plugin.action()
def favorites(params):
	from resources.lib import favorites
	favorites.Fav().run(params)


@plugin.action()
def fav_manager(params):
	from resources.lib import gui
	gui.favorites_manager(params)


@plugin.action()
def media_info():
	import xbmc
	xbmc.executebuiltin('Action(Info)')


@plugin.action()
def settings_open():
	addon.addon.openSettings()
	prop = addon.get_mem_storage(addon.name)
	prop.clear()


@plugin.action()
def cache_clear_meta():
	from resources.lib import gui
	gui.cache_clear_meta()


@plugin.action()
def cache_clear_memory():
	from resources.lib import gui
	gui.cache_clear_memory()


@plugin.action()
def changelog_txt():
	from resources.lib import gui
	gui.changelog_txt()


@plugin.action()
def trakt_authorize():
	from resources.lib import gui
	gui.trakt_authorize()


@plugin.action()
def trakt_revoke():
	from resources.lib import gui
	gui.trakt_revoke()


@plugin.action()
def trakt_account_stats():
	from resources.lib import gui
	gui.trakt_account_stats()


@plugin.action()
def test_func():
	pass

# An action can take an optional argument that contain
# plugin call parameters parsed into a dict-like object.
# The params object allows to access parameters by key or by attribute
@plugin.action()
def play(params):
	"""Play video"""
	import xbmcgui, xbmcplugin
	li = xbmcgui.ListItem(path=params.video)
	xbmcplugin.setResolvedUrl(plugin.handle, True, li)


@plugin.action('root')
def example_root(params):
	"""
	Root virtual folder

	This is a mandatory item.
	"""
	from resources.lib.example import Example
	Example(params)
