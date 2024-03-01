from resources.external.simpleplugin import Addon
from resources.lib.common import Gui, UNAIRED_COLOR


addon, gui = Addon(), Gui()


def cache_clear_meta():
	from resources.lib import metadata

	if not gui.confirm(): return
	try:
		metadata.MetaCache().clear_tables()
		gui.notify_success()
	except:
		gui.notify_fail()


def cache_clear_memory():
	if not gui.confirm(): return
	try:
		prop = addon.get_mem_storage('***cache***')
		prop.clear()
		gui.notify_success()
	except:
		gui.notify_fail()


def changelog_txt():
	from pprint import pformat

	with open(f"{addon.path}changelog.txt") as file: log = file.read()
	prop = pformat(dict(addon.get_mem_storage(addon.name)))
	text = '\n\n'.join((prop, log)) # probably just want to view log variable in normal use
	gui.textviewer('CHANGELOG', text, True)


def favorites_manager(params):
	from resources.lib import favorites

	media = params['media']
	tmdb_id = params.get('tmdb_id')
	list_id = params.get('list_id')
	title = params['title']
	db = favorites.Favorites()
	data = db.get(tmdb_id or list_id)
	if data:
		if not gui.confirm('Remove from favorites?'): return
		db.remove(media, tmdb_id or list_id)
		gui.notify_success()
		gui.refresh()
	else:
		if not gui.confirm('Add to favorites?'): return
		db.set(media, tmdb_id or list_id, title)
		gui.notify_success()


def trakt_authorize():
	import time
	from resources.lib import trakt

	trakt_account = trakt.Account()
	response = trakt_account._get_device_code()
	device_code = response['device_code']
	expires_in = int(response['expires_in'])
	sleep_interval = int(response['interval'])
	verification_url = UNAIRED_COLOR % response['verification_url']
	user_code = UNAIRED_COLOR % response['user_code']
	service = UNAIRED_COLOR % 'Trakt'
	dialog_text = f"Authorize Service: {service}\nNavigate to: {verification_url}\nEnter code: {user_code}"
	dialog = gui.progress_dialog()
	dialog.create(addon.name, dialog_text)
	token = ''
	time_passed = expires_in
	while not token and not dialog.iscanceled() and time_passed:
		dialog.update(int(time_passed / expires_in * 100))
		gui.sleep(1000)
		time_passed -= 1
		if time_passed % sleep_interval: continue
		token = trakt_account._get_device_token(code=device_code)
	try: dialog.close()
	except: pass
	if not token: return gui.notify_fail()
	refresh = token['refresh_token']
	token = token['access_token']
	expires = int(time.time() + 7776000)
	gui.sleep(1000)
	trakt_account.headers['Authorization'] = f"Bearer {token}"
	response = trakt_account.whoami()
	username = response['username']
	addon.set_setting('trakt_refresh', refresh)
	addon.set_setting('trakt_token', token)
	addon.set_setting('trakt_expires', expires)
	addon.set_setting('trakt_username', username)
	prop = addon.get_mem_storage(addon.name)
	prop['trakt_token'] = token
	gui.refresh()
	return gui.notify_success()


def trakt_revoke():
	from resources.lib import trakt

	if not gui.confirm(): return
	respose = trakt.Account().revoke_authorization()
	addon.set_setting('trakt_refresh', '')
	addon.set_setting('trakt_token', '')
	addon.set_setting('trakt_expires', '')
	addon.set_setting('trakt_username', '')
	prop = addon.get_mem_storage(addon.name)
	del prop['trakt_token']
	gui.refresh()
	return gui.notify_success()


def trakt_account_stats():
	from resources.lib import trakt

	trakt_account = trakt.Account()
	account_info = trakt_account.settings()
	username, userslug = account_info['user']['username'], account_info['user']['ids']['slug']
	stats = trakt_account.stats(userslug)
	timezone = account_info['account']['timezone']
	joined = account_info['user']['joined_at'][:10]
	location = account_info['user']['location']
	private, vip = account_info['user']['private'], account_info['user']['vip']
	total_given_ratings = stats['ratings']['total']
	movies_collected = stats['movies']['collected']
	movies_watched = stats['movies']['watched']
	movie_minutes = stats['movies']['minutes']
	shows_collected = stats['shows']['collected']
	shows_watched = stats['shows']['watched']
	episodes_watched = stats['episodes']['watched']
	episode_minutes = stats['episodes']['minutes']
	items = []
	items += ['[B]Username:[/B] %s' % username]
	items += ['[B]Location:[/B] %s' % location]
	items += ['[B]Timezone:[/B] %s' % timezone]
	items += ['[B]Joined:[/B] %s' % joined]
	items += ['[B]Private:[/B] %s' % private]
	items += ['[B]VIP Status:[/B] %s' % vip]
	items += ['[B]Ratings Given:[/B] %s' % str(total_given_ratings)]
	items += ['[B]Movies:[/B] [B]%s[/B] Collected, [B]%s[/B] Watched' % (movies_collected, movies_watched)]
	items += ['[B]Shows:[/B] [B]%s[/B] Collected, [B]%s[/B] Watched' % (shows_collected, shows_watched)]
	items += ['[B]Episodes:[/B] [B]%s[/B] Watched' % (episodes_watched)]
	gui.textviewer('Trakt User Stats', '\n\n'.join(items), True)
