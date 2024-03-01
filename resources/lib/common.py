from concurrent.futures import ThreadPoolExecutor
import os

import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs


Actor = xbmc.Actor
Addon = xbmcaddon.Addon
addon = xbmcaddon.Addon()

delete = xbmcvfs.delete
exists = xbmcvfs.exists
mkdir = xbmcvfs.mkdir
transPath = xbmcvfs.translatePath
joinPath = os.path.join

THREADS = 21
UNAIRED_COLOR = '[COLOR cyan]%s[/COLOR]'
context = {
	'favs': UNAIRED_COLOR % 'Favorites Manager'
}


def logger(message, depth=None):
	from pprint import pformat
	prefix = f"[ {addon.getAddonInfo('id')} ]"
	if isinstance(message, str): xbmc.log(f"{prefix}: {message}", xbmc.LOGINFO)
	else: xbmc.log(f"{prefix}: \n{pformat(message, depth=depth)}", xbmc.LOGINFO)


def get_handle():
	import sys
	return int(sys.argv[1])


def addon_name():
	return addon.getAddonInfo('name')


def profile_path():
	return transPath(addon.getAddonInfo('profile'))


class Gui(xbmcgui.Dialog):
	name = addon_name()

	def notify(self, message, heading='', time=2000, icon=''):
		heading = heading or self.name
		icon = icon or xbmcgui.NOTIFICATION_INFO
		self.notification(heading=heading, message=message, time=time, icon=icon)

	def notify_success(self, message='SUCCESS'):
		self.notify(message)
		return True

	def notify_fail(self, message='FAILED'):
		icon = xbmcgui.NOTIFICATION_WARNING
		self.notify(message, icon=icon)
		return False

	def confirm(self, message='', heading=''):
		heading = heading or self.name
		message = message or 'Are you sure?'
		return self.yesno(heading=heading, message=message)

	@staticmethod
	def refresh():
		xbmc.executebuiltin('Container.Refresh')

	@staticmethod
	def sleep(time=1000):
		xbmc.sleep(time)

	@staticmethod
	def progress_dialog():
		return xbmcgui.DialogProgress()


class Container:
	Pool = ThreadPoolExecutor
	threads = THREADS
	meth = {
		'episodes': xbmcplugin.SORT_METHOD_EPISODE
	}

	def __init__(self, name=None):
		self.category = name or ''
		self.content = 'files'
		self.item_list = []
		self.unsorted = False

	@property
	def sort_method(self):
		return self.meth.get(self.content, xbmcplugin.SORT_METHOD_UNSORTED)

	def end(self, cacheToDisc=True):
		handle = get_handle()
		sort_how = xbmcplugin.SORT_METHOD_UNSORTED if self.unsorted else self.sort_method
		xbmcplugin.addDirectoryItems(handle, self.item_list)
		xbmcplugin.addSortMethod(handle, sort_how)
		xbmcplugin.setPluginCategory(handle, self.category)
		xbmcplugin.setContent(handle, self.content)
		xbmcplugin.endOfDirectory(handle, cacheToDisc=cacheToDisc)

	@staticmethod
	def make_listitem(label=''):
		return xbmcgui.ListItem(label=label, offscreen=True)
