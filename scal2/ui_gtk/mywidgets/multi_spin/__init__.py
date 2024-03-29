# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux

import sys, os
from time import localtime
from time import time as now

from scal2.utils import toStr, toUnicode
from scal2.cal_types import to_jd, jd_to
from scal2 import locale_man
from scal2.locale_man import tr as _
from scal2.mywidgets.multi_spin import * ## FIXME
from scal2 import ui

from gobject import timeout_add

from scal2.ui_gtk import *
from scal2.ui_gtk.decorators import *

@registerSignals
class MultiSpinButton(gtk.SpinButton):
	signals = [
		('first-min', []),
		('first-max', []),
	]
	def __init__(self, sep, fields, arrow_select=True, page_inc=10):
		gtk.SpinButton.__init__(self)
		####
		sep = toUnicode(sep)
		self.field = ContainerField(sep, *fields)
		self.arrow_select = arrow_select
		self.set_editable(True)
		###
		self.digs = locale_man.getDigits()
		###
		####
		self.set_direction(gtk.TEXT_DIR_LTR) ## self is a gtk.Entry
		self.set_width_chars(self.field.getMaxWidth())
		self.set_value(0)
		self.set_digits(0)
		gtk.SpinButton.set_range(self, -2, 2)
		self.set_increments(1, page_inc)
		#self.connect('activate', lambda obj: self.update())
		self.connect('activate', self._entry_activate)
		self.connect('key-press-event', self._key_press)
		self.connect('scroll-event', self._scroll)
		self.connect('button-press-event', self._button_press)
		self.connect('button-release-event', self._button_release)
		self.connect('output', lambda obj: True)##Disable auto-numeric-validating(the entry text is not a numebr)
		####
		#self.select_region(0, 0)
	def _entry_activate(self, widget):
		#print('_entry_activate', self.get_text())
		self.update()
		#print(self.get_text())
		return True
	def get_value(self):
		self.field.setText(self.get_text())
		return self.field.getValue()
	def set_value(self, value):
		pos = self.get_position()
		self.field.setValue(value)
		self.set_text(self.field.getText())
		self.set_position(pos)
	def update(self):
		pos = self.get_position()
		self.field.setText(toUnicode(self.get_text()))
		self.set_text(self.field.getText())
		self.set_position(pos)
	def insertText(self, s, clearSeceltion=True):
		selection = self.get_selection_bounds()
		if selection and clearSeceltion:
			start, end = selection
			text = toUnicode(self.get_text())
			text = text[:start] + s + text[end:]
			self.set_text(text)
			self.set_position(start+len(s))
		else:
			pos = self.get_position()
			self.insert_text(s, pos)
			self.set_position(pos + len(s))
	def entry_plus(self, p):
		self.update()
		pos = self.get_position()
		self.field.getFieldAt(toUnicode(self.get_text()), self.get_position()).plus(p)
		self.set_text(self.field.getText())
		self.set_position(pos)
	def _key_press(self, widget, gevent):
		kval = gevent.keyval
		kname = gdk.keyval_name(kval).lower()
		size = len(self.field)
		sep = self.field.sep
		step_inc, page_inc = self.get_increments()
		if kname in ('up', 'down', 'page_up', 'page_down', 'left', 'right'):
			if not self.get_editable():
				return True
			if kname in ('left', 'right'):
				return False
				#if not self.arrow_select:
				#	return False
				#shift = {
				#	'left': -1,
				#	'right': 1
				#}[kname]
				#FIXME
			else:
				p = {
					'up': step_inc,
					'down': -step_inc,
					'page_up': page_inc,
					'page_down': -page_inc,
				}[kname]
				self.entry_plus(p)
			#from scal2.utils import strFindNth
			#if fieldIndex==0:
			#	i1 = 0
			#else:
			#	i1 = strFindNth(text, sep, fieldIndex) + len(sep)
			#i2 = strFindNth(text, sep, fieldIndex+1)
			##self.grab_focus()
			#self.select_region(i1, i2)
			return True
		#elif kname=='return':## Enter
		#	self.update()
		#	##self.emit('activate')
		#	return True
		elif ord('0') <= kval <= ord('9'):
			self.insertText(self.digs[kval-ord('0')])
			return True
		elif 'kp_0' <= kname <= 'kp_9':
			self.insertText(self.digs[int(kname[-1])])
			return True
		elif kname in (
			'period', 'kp_decimal',
		):
			self.insertText(locale_man.getNumSep())
			return True
		else:
			#print(kname, kval)
			return False
	def _button_press(self, widget, gevent):
		gwin = gevent.window
		#print(gwin.get_data('name'))
		#r = self.get_allocation() ; print('allocation', r[0], r[2])
		if not self.has_focus():
			self.grab_focus()
		if self.get_editable():
			self.update()
		height = self.size_request()[1]
		step_inc, page_inc = self.get_increments()
		if gwin.get_position()[1] == 0:## the panel window (containing up and down arrows)
			## gwin.xid == self.get_window().get_children()[0].xid ## the same as _gtk_spin_button_get_panel
			if gevent.y*2 < height:
				if gevent.button==1:
					self._arrow_press(step_inc)
				elif gevent.button==2:
					self._arrow_press(page_inc)
			else:
				if gevent.button==1:
					self._arrow_press(-step_inc)
				else:
					self._arrow_press(-page_inc)
			return True
		else:
			if gevent.type==TWO_BUTTON_PRESS:
				pass ## FIXME
				## select the numeric part containing cursor
				#return True
		return False
	def _scroll(self, widget, gevent):
		d = gevent.direction.value_nick
		if d in ('up', 'down'):
			if not self.has_focus():
				self.grab_focus()
			if self.get_editable():
				self.entry_plus((1 if d=='up' else -1)*self.get_increments()[0])
		else:
			return False
		return True
	#def _move_cursor(self, obj, step, count, extend_selection):
		## force_select
		#print'_entry_move_cursor', count, extend_selection
	def _arrow_press(self, plus):
		self.pressTm = now()
		self._remain = True
		timeout_add(ui.timeout_initial, self._arrow_remain, plus)
		self.entry_plus(plus)
	def _arrow_remain(self, plus):
		if self.get_editable() and self._remain and now()-self.pressTm>=ui.timeout_repeat/1000.0:
			self.entry_plus(plus)
			timeout_add(ui.timeout_repeat, self._arrow_remain, plus)
	def _button_release(self, widget, gevent):
		self._remain = False
	"""## ????????????????????????????????
	def _arrow_enter_notify(self, gtkWin):
		if gtkWin!=None:
			print('_arrow_enter_notify')
			gtkWin.set_background(gdk.Color(-1, 0, 0))
			gtkWin.show()
	def _arrow_leave_notify(self, gtkWin):
		if gtkWin!=None:
			print('_arrow_leave_notify')
			gtkWin.set_background(gdk.Color(-1, -1, -1))
	#"""


class SingleSpinButton(MultiSpinButton):
	def __init__(self, field, **kwargs):
		MultiSpinButton.__init__(
			self,
			' ',
			(field,),
			**kwargs
		)
	get_value = lambda self: MultiSpinButton.get_value(self)[0]


