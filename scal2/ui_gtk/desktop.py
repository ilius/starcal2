# -*- coding: utf-8 -*-
#
# Copyright (C) 2003 Martin Grimme <martin@pycage.de>
#				and Sebastien Bacher <seb128@debian.org>
#				as part of package gdeskcal http://www.pycage.de/software_gdeskcal.html
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

import gtk
root = gtk.gdk.get_default_root_window()
wid = 0

#
# Restricts the given coordinates to visible values.
#
def _crop_coords(x, y, w, h):
	sw = gtk.gdk.screen_width()
	sh = gtk.gdk.screen_height()
	x = min(x, sw-1)
	y = min(y, sh-1)
	return (x, y, min(sw-x, w), min(sh-y, h))



#
# Captures solid color wallpapers. Requires GNOME.
#
def get_wallcolor(width, height):
	import gconf
	client = gconf.client_get_default()
	client.add_dir("/desktop/gnome/background", gconf.CLIENT_PRELOAD_RECURSIVE)
	value = client.get("/desktop/gnome/background/primary_color")
	color = value.get_string()

	pbuf = gtk.gdk.Pixbuf(0, 1, 8, width, height)
	c = gtk.gdk.color_parse(color)
	fillr = (c.red / 256) << 24
	fillg = (c.green / 256) << 16
	fillb = (c.blue / 256) << 8
	fillcolor = fillr | fillg | fillb | 255
	pbuf.fill(fillcolor)

	return pbuf



#
# Captures the wallpaper image by making a screen shot.
#
def get_wallpaper_fallback(x, y, width, height):

	x, y, width, height = _crop_coords(x, y, width, height)

	pbuf = gtk.gdk.Pixbuf(0, 1, 8, width, height)
	pbuf.get_from_drawable(root, root.get_colormap(),
						   x, y, 0, 0, width, height)
	return pbuf



#
# Captures the wallpaper image by accessing the background pixmap.
#
def get_wallpaper(x, y, width, height):
	x, y, width, height = _crop_coords(x, y, width, height)

	# get wallpaper
	pmap_id = get_wallpaper_id()
	if hasattr(gtk.gdk, "gdk_pixmap_foreign_new"):
		pmap = gtk.gdk.gdk_pixmap_foreign_new(pmap_id)
	else:
		pmap = gtk.gdk.pixmap_foreign_new(pmap_id)
	pwidth, pheight = pmap.get_size()

	# create pixbuf
	pbuf = gtk.gdk.Pixbuf(0, 1, 8, width, height)

	# tile wallpaper over pixbuf
	sx = -(x % pwidth)
	sy = -(y % pheight)
	for x in range(sx, width, pwidth):
		for y in range(sy, height, pheight):
			dstx = max(0, x)
			dsty = max(0, y)
			srcx = dstx - x
			srcy = dsty - y

			w = min(pwidth - srcx, width - dstx)
			h = min(pheight - srcy, height - dsty)

			pbuf.get_from_drawable(pmap, root.get_colormap(),
								   srcx, srcy, dstx, dsty, w, h)

	return pbuf




#
# Returns the ID of the background pixmap.
#
def get_wallpaper_id():
	global wid
	try:
		wid = root.property_get("_XROOTPMAP_ID", "PIXMAP")[2][0]
		return long(wid)

	except:
		#raise NotImplementedError
		return long(wid)



def watch_bg(observer):
	_BGWATCHER.add_observer(observer)


#from BGWatcher import BGWatcher
#_BGWATCHER = BGWatcher()
