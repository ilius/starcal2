# -*- coding: utf-8 -*-
#
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

import sys, os
from os.path import join, split, isabs

from scal2.path import *
from scal2.utils import toStr, toUnicode
from scal2.cal_types import calTypes
from scal2 import core
from scal2 import locale_man
from scal2.locale_man import langDict, langSh, rtl
from scal2.locale_man import tr as _
from scal2 import startup
from scal2 import ui

from scal2.ui_gtk import *
from scal2.ui_gtk.font_utils import *
from scal2.ui_gtk.color_utils import *
from scal2.ui_gtk.utils import *


from scal2.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal2.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton



## (VAR_NAME, bool,     CHECKBUTTON_TEXT)                 ## CheckButton
## (VAR_NAME, list,     LABEL_TEXT, (ITEM1, ITEM2, ...))  ## ComboBox
## (VAR_NAME, int,      LABEL_TEXT, MIN, MAX)             ## SpinButton
## (VAR_NAME, float,    LABEL_TEXT, MIN, MAX, DIGITS)     ## SpinButton
class ModuleOptionItem:
	def __init__(self, module, opt):
		t = opt[1]
		self.opt = opt ## needed??
		self.module = module
		self.type = t
		self.var_name = opt[0]
		hbox = gtk.HBox()
		if t==bool:
			w = gtk.CheckButton(_(opt[2]))
			self.get_value = w.get_active
			self.set_value = w.set_active
		elif t==list:
			pack(hbox, gtk.Label(_(opt[2])))
			w = gtk.combo_box_new_text() ### or RadioButton
			for s in opt[3]:
				w.append_text(_(s))
			self.get_value = w.get_active
			self.set_value = w.set_active
		elif t==int:
			pack(hbox, gtk.Label(_(opt[2])))
			w = IntSpinButton(opt[3], opt[4])
			self.get_value = w.get_value
			self.set_value = w.set_value
		elif t==float:
			pack(hbox, gtk.Label(_(opt[2])))
			w = FloatSpinButton(opt[3], opt[4], opt[5])
			self.get_value = w.get_value
			self.set_value = w.set_value
		else:
			raise RuntimeError('bad option type "%s"'%t)
		pack(hbox, w)
		self._widget = hbox
		####
		self.updateVar = lambda: setattr(self.module, self.var_name, self.get_value())
		self.updateWidget = lambda: self.set_value(getattr(self.module, self.var_name))

	def getWidget(self):
		return self._widget


## ('button', LABEL, CLICKED_MODULE_NAME, CLICKED_FUNCTION_NAME)
class ModuleOptionButton:
	def __init__(self, opt):
		funcName = opt[2]
		clickedFunc = getattr(__import__('scal2.ui_gtk.%s'%opt[1], fromlist=[funcName]), funcName)
		hbox = gtk.HBox()
		button = gtk.Button(_(opt[0]))
		button.connect('clicked', clickedFunc)
		pack(hbox, button)
		self._widget = hbox
	def updateVar(self):
		pass
	def updateWidget(self):
		pass

	def getWidget(self):
		return self._widget


class PrefItem():
	## self.__init__, self.module, self.varName, self._widget
	## self.varName an string containing the name of variable
	## set self.module=None if varName is name of a global variable in this module
	def get(self):
		raise NotImplementedError
	def set(self, value):
		raise NotImplementedError
	updateVar = lambda self: setattr(self.module, self.varName, self.get())
	updateWidget = lambda self: self.set(getattr(self.module, self.varName))
	## confStr(): gets the value from variable (not from GUI) and returns a string to save to file
	## the string will has a NEWLINE at the END
	def confStr(self):
		value = getattr(self.module, self.varName)
		if isinstance(value, str):
			value = toUnicode(value)
		valueStr = repr(value)
		## repr of a utf8 string (by Python 2) is not utf8 and not readable correctly from Python 3
		## no simple way you can fix that for strings nested inside other structures
		## yet another reason to switch to JSON for config files
		## FIXME
		return '%s=%s\n'%(self.varName, valueStr)

	def getWidget(self):
		return self._widget


class ComboTextPrefItem(PrefItem):
	def makeWidget(self):
		return gtk.combo_box_new_text()
	def __init__(self, module, varName, items=[]):## items is a list of strings
		self.module = module
		self.varName = varName
		w = self.makeWidget()
		self._widget = w
		for s in items:
			w.append_text(s)
	get = lambda self: self._widget.get_active()
	set = lambda value: self._widget.set_active(value)
	#def set(self, value):
	#	print('ComboTextPrefItem.set', value)
	#	self._widget.set_active(int(value))

class FontFamilyPrefItem(ComboTextPrefItem):
	def makeWidget(self):
		from scal2.ui_gtk.mywidgets.font_family_combo import FontFamilyCombo
		return FontFamilyCombo(True)
	get = lambda self: self._widget.get_value()
	set = lambda self, value: self._widget.set_value(value)

class ComboEntryTextPrefItem(PrefItem):
	def __init__(self, module, varName, items=[]):## items is a list of strings
		self.module = module
		self.varName = varName
		w = gtk.combo_box_entry_new_text()
		self._widget = w
		for s in items:
			w.append_text(s)
		child = w.get_child()
		self.get = child.get_text
		self.set = child.set_text

class ComboImageTextPrefItem(PrefItem):
	def __init__(self, module, varName, items=[]):## items is a list of pairs (imagePath, text)
		self.module = module
		self.varName = varName
		###
		ls = gtk.ListStore(gdk.Pixbuf, str)
		combo = gtk.ComboBox()
		combo.set_model(ls)
		###
		cell = gtk.CellRendererPixbuf()
		pack(combo, cell, False)
		combo.add_attribute(cell, 'pixbuf', 0)
		###
		cell = gtk.CellRendererText()
		pack(combo, cell, True)
		combo.add_attribute(cell, 'text', 1)
		###
		self._widget = combo
		self.ls = ls
		for (imPath, label) in items:
			self.append(imPath, label)
		self.get = combo.get_active
		self.set = combo.set_active
	def append(self, imPath, label):
		if imPath:
			if not isabs(imPath):
				imPath = join(pixDir, imPath)
			pix = gdk.pixbuf_new_from_file(imPath)
		else:
			pix = None
		self.ls.append([pix, label])


class FontPrefItem(PrefItem):##????????????
	def __init__(self, module, varName, parent):
		from scal2.ui_gtk.mywidgets import MyFontButton
		self.module = module
		self.varName = varName
		w = MyFontButton(parent)
		self._widget = w
		self.get = w.get_font_name## FIXME
		self.set = w.set_font_name## FIXME

class CheckPrefItem(PrefItem):
	def __init__(self, module, varName, label='', tooltip=None):
		self.module = module
		self.varName = varName
		w = gtk.CheckButton(label)
		if tooltip!=None:
			set_tooltip(w, tooltip)
		self._widget = w
		self.get = w.get_active
		self.set = w.set_active
	def syncSensitive(self, widget, reverse=False):
		self._sensitiveWidget = widget
		self._sensitiveReverse = reverse
		self._widget.connect('show', self.syncSensitiveUpdate)
		self._widget.connect('clicked', self.syncSensitiveUpdate)
	def syncSensitiveUpdate(self, myWidget):
		active = myWidget.get_active()
		if self._sensitiveReverse:
			active = not active
		self._sensitiveWidget.set_sensitive(active)


class LiveCheckPrefItem(CheckPrefItem):
	def __init__(self, module, varName, label="", tooltip="", onChangeFunc=None):
		CheckPrefItem.__init__(self, module, varName, label=label, tooltip=tooltip)
		self._onChangeFunc = onChangeFunc
		# updateWidget needs to be called before following connect() calls
		self.updateWidget()
		self._widget.connect("clicked", self.onClicked)

	def onClicked(self, w):
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()


class ColorPrefItem(PrefItem):
	def __init__(self, module, varName, useAlpha=False):
		from scal2.ui_gtk.mywidgets import MyColorButton
		self.module = module
		self.varName = varName
		w = MyColorButton()
		w.set_use_alpha(useAlpha)
		self.useAlpha = useAlpha
		self._widget = w
		self.set = w.set_color
	def get(self):
		#if self.useAlpha:
		alpha = self._widget.get_alpha()
		if alpha==None:
			return self._widget.get_color()
		else:
			return self._widget.get_color() + (alpha,)
	def set(self, color):
		if self.useAlpha:
			if len(color)==3:
				self._widget.set_color(color)
				self._widget.set_alpha(255)
			elif len(color)==4:
				self._widget.set_color(color[:3])
				self._widget.set_alpha(color[3])
			else:
				raise ValueError
		else:
			self._widget.set_color(color)

class LiveColorPrefItem(ColorPrefItem):
	def __init__(self, module, varName, useAlpha=False, onChangeFunc=None):
		ColorPrefItem.__init__(self, module, varName, useAlpha=useAlpha)
		self._onChangeFunc = onChangeFunc
		# updateWidget needs to be called before following connect() calls
		self.updateWidget()
		self._widget.connect("color-set", self.onColorSet)

	def onColorSet(self, w):
		self.updateVar()
		if self._onChangeFunc:
			self._onChangeFunc()

# combination of CheckPrefItem and ColorPrefItem in a HBox, with auto-update / auto-apply, for use in Customize window
class LiveCheckColorPrefItem(PrefItem):
	def __init__(
		self,
		checkItem, # type: CheckPrefItem
		colorItem, # type: ColorPrefItem
		onChangeFunc = None, # type: Optional[Callable]
		checkSizeGroup = None, # type: Optional[gtk.SizeGroup]
	):
		self._checkItem = checkItem
		self._colorItem = colorItem
		self._onChangeFunc = onChangeFunc

		checkb = self._checkItem.getWidget()
		colorb = self._colorItem.getWidget()

		if checkSizeGroup:
			checkSizeGroup.add_widget(checkb)

		hbox = HBox(spacing=3)
		pack(hbox, checkb)
		pack(hbox, colorb)
		self._widget = hbox

		# updateWidget needs to be called before following connect() calls
		self.updateWidget()

		checkb.connect("clicked", self.onChange)
		colorb.connect("color-set", self.onChange)

	def updateVar(self):
		self._checkItem.updateVar()
		self._colorItem.updateVar()

	def updateWidget(self):
		# FIXME: this func is triggering onChange func, can we avoid that?
		self._checkItem.updateWidget()
		self._colorItem.updateWidget()
		self._colorItem.getWidget().set_sensitive(self._checkItem.get())

	def onChange(self, w):
		self.updateVar()
		self._colorItem.getWidget().set_sensitive(self._checkItem.get())
		if self._onChangeFunc:
			self._onChangeFunc()


class SpinPrefItem(PrefItem):
	def __init__(self, module, varName, _min, _max, digits=1):
		self.module = module
		self.varName = varName
		if digits==0:
			w = IntSpinButton(_min, _max)
		else:
			w = FloatSpinButton(_min, _max, digits)
		self._widget = w
		self.get = w.get_value
		self.set = w.set_value

class WidthHeightPrefItem(PrefItem):
	def __init__(self, module, varName, _max):
		_min = 0
		self.module = module
		self.varName = varName
		###
		self.widthItem = IntSpinButton(_min, _max)
		self.heightItem = IntSpinButton(_min, _max)
		###
		hbox = self._widget = gtk.HBox()
		pack(hbox, gtk.Label(_('Width')+':'))
		pack(hbox, self.widthItem)
		pack(hbox, gtk.Label('  '))
		pack(hbox, gtk.Label(_('Height')+':'))
		pack(hbox, self.heightItem)
	def get(self):
		return (
			int(self.widthItem.get_value()),
			int(self.heightItem.get_value()),
		)
	def set(self, value):
		w, h = value
		self.widthItem.set_value(w)
		self.heightItem.set_value(h)


class FileChooserPrefItem(PrefItem):
	def __init__(self, module, varName, title='Select File', currentFolder='', defaultVarName=None):
		self.module = module
		self.varName = varName
		###
		dialog = gtk.FileChooserDialog(title, action=gtk.FILE_CHOOSER_ACTION_OPEN)
		dialog_add_button(dialog, gtk.STOCK_CANCEL, _('_Cancel'), gtk.RESPONSE_CANCEL, None)
		dialog_add_button(dialog, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK, None)
		w = gtk.FileChooserButton(dialog)
		w.set_local_only(True)
		if currentFolder:
			w.set_current_folder(currentFolder)
		###
		self.defaultVarName = defaultVarName
		if defaultVarName:
			dialog_add_button(dialog, gtk.STOCK_UNDO, _('_Revert'), gtk.RESPONSE_NONE, self.revertClicked)
		###
		self._widget = w
		self.get = w.get_filename
		self.set = w.set_filename
	def revertClicked(self, button):
		defaultValue = getattr(self.module, self.defaultVarName)
		setattr(
			self.module,
			self.varName,
			defaultValue,
		)
		self.set(defaultValue)


class RadioListPrefItem(PrefItem):
	def __init__(self, vertical, module, varName, texts, label=None):
		self.num = len(texts)
		self.module = module
		self.varName = varName
		if vertical:
			box = gtk.VBox()
		else:
			box = gtk.HBox()
		self._widget = box
		self.radios = [gtk.RadioButton(label=_(s)) for s in texts]
		first = self.radios[0]
		if label!=None:
			pack(box, gtk.Label(label))
			pack(box, gtk.Label(''), 1, 1)
		pack(box, first)
		for r in self.radios[1:]:
			pack(box, gtk.Label(''), 1, 1)
			pack(box, r)
			r.set_group(first)
		pack(box, gtk.Label(''), 1, 1) ## FIXME
	def get(self):
		for i in range(self.num):
			if self.radios[i].get_active():
				return i
	def set(self, index):
		self.radios[index].set_active(True)

class RadioHListPrefItem(RadioListPrefItem):
	def __init__(self, *args, **kwargs):
		RadioListPrefItem.__init__(self, False, *args, **kwargs)

class RadioVListPrefItem(RadioListPrefItem):
	def __init__(self, *args, **kwargs):
		RadioListPrefItem.__init__(self, True, *args, **kwargs)


class ListPrefItem(PrefItem):
	def __init__(self, vertical, module, varName, items=[]):
		self.module = module
		self.varName = varName
		if vertical:
			box = gtk.VBox()
		else:
			box = gtk.HBox()
		for item in items:
			pack(box, item._widget)
		self.num = len(items)
		self.items = items
		self._widget = box
	get = lambda self: [item.get() for item in self.items]
	def set(self, valueL):
		for i in range(self.num):
			self.items[i].set(valueL[i])
	def append(self, item):
		pack(self._widget, item._widget)
		self.items.append(item)


class HListPrefItem(ListPrefItem):
	def __init__(self, *args, **kwargs):
		ListPrefItem.__init__(self, False, *args, **kwargs)

class VListPrefItem(ListPrefItem):
	def __init__(self, *args, **kwargs):
		ListPrefItem.__init__(self, True, *args, **kwargs)


class WeekDayCheckListPrefItem(PrefItem):
	def __init__(self, module, varName, vertical=False, homo=True, abbreviateNames=True):
		self.module = module
		self.varName = varName
		if vertical:
			box = gtk.VBox()
		else:
			box = gtk.HBox()
		box.set_homogeneous(homo)
		nameList = core.weekDayNameAb if abbreviateNames else core.weekDayName
		ls = [gtk.ToggleButton(item) for item in nameList]
		s = core.firstWeekDay
		for i in range(7):
			pack(box, ls[(s+i)%7], 1, 1)
		self.cbList = ls
		self._widget = box
		self.start = s
	def setStart(self, s):
		b = self._widget
		ls = self.cbList
		for j in range(7):## or range(6)
			b.reorder_child(ls[(s+j)%7], j)
		self.start = s
	def get(self):
		value = []
		cbl = self.cbList
		for j in range(7):
			if cbl[j].get_active():
				value.append(j)
		return value
	def set(self, value):
		cbl = self.cbList
		for cb in cbl:
			cb.set_active(False)
		for j in value:
			cbl[j].set_active(True)


'''
class ToolbarIconSizePrefItem(PrefItem):
	def __init__(self, module, varName):
		self.module = module
		self.varName = varName
		####
		self._widget = gtk.combo_box_new_text()
		for item in ud.iconSizeList:
			self._widget.append_text(item[0])
	get = lambda self: ud.iconSizeList[self._widget.get_active()][0]
	def set(self, value):
		for (i, item) in enumerate(ud.iconSizeList):
			if item[0]==value:
				self._widget.set_active(i)
				return
'''

############################################################

class LangPrefItem(PrefItem):
	def __init__(self):
		self.module = locale_man
		self.varName = 'lang'
		###
		ls = gtk.ListStore(gdk.Pixbuf, str)
		combo = gtk.ComboBox()
		combo.set_model(ls)
		###
		cell = gtk.CellRendererPixbuf()
		pack(combo, cell, False)
		combo.add_attribute(cell, 'pixbuf', 0)
		###
		cell = gtk.CellRendererText()
		pack(combo, cell, True)
		combo.add_attribute(cell, 'text', 1)
		###
		self._widget = combo
		self.ls = ls
		self.append(join(pixDir, 'computer.png'), _('System Setting'))
		for (key, data) in langDict.items():
			self.append(data.flag, data.name)
	def append(self, imPath, label):
		if imPath=='':
			pix = None
		else:
			if not isabs(imPath):
				imPath = join(pixDir, imPath)
			pix = gdk.pixbuf_new_from_file(imPath)
		self.ls.append([pix, label])
	def get(self):
		i = self._widget.get_active()
		if i==0:
			return ''
		else:
			return langDict.keyList[i-1]
	def set(self, value):
		if value=='':
			self._widget.set_active(0)
		else:
			try:
				i = langDict.keyList.index(value)
			except ValueError:
				print('language %s in not in list!'%value)
				self._widget.set_active(0)
			else:
				self._widget.set_active(i+1)
	#def updateVar(self):
	#	lang =

class CheckStartupPrefItem():## FIXME
	def __init__(self):
		w = gtk.CheckButton(_('Run on session startup'))
		set_tooltip(w, 'Run on startup of Gnome, KDE, Xfce, LXDE, ...\nFile: %s'%startup.comDesk)
		self._widget = w
		self.get = w.get_active
		self.set = w.set_active
	def updateVar(self):
		if self.get():
			if not startup.addStartup():
				self.set(False)
		else:
			try:
				startup.removeStartup()
			except:
				pass
	def updateWidget(self):
		self.set(startup.checkStartup())
	confStr = lambda self: ''

class AICalsTreeview(gtk.TreeView):
	def __init__(self):
		gtk.TreeView.__init__(self)
		self.set_headers_clickable(False)
		self.set_model(gtk.ListStore(str, str))
		###
		self.enable_model_drag_source(
			gdk.BUTTON1_MASK,
			[
				('row', gtk.TARGET_SAME_APP, self.dragId),
			],
			gdk.ACTION_MOVE,
		)
		self.enable_model_drag_dest(
			[
				('row', gtk.TARGET_SAME_APP, self.dragId),
			],
			gdk.ACTION_MOVE,
		)
		self.connect('drag-data-get', self.dragDataGet)
		self.connect('drag_data_received', self.dragDataReceived)
		####
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(self.title, cell, text=1)
		col.set_resizable(True)
		self.append_column(col)
		self.set_search_column(1)
	def dragDataGet(self, treev, context, selection, dragId, etime):
		path, col = treev.get_cursor()
		if path is None:
			return
		self.dragPath = path
		return True
	def dragDataReceived(self, treev, context, x, y, selection, dragId, etime):
		srcTreev = context.get_source_widget()
		if not isinstance(srcTreev, AICalsTreeview):
			return
		srcDragId = srcTreev.dragId
		model = treev.get_model()
		dest = treev.get_dest_row_at_pos(x, y)
		if srcDragId == self.dragId:
			path, col = treev.get_cursor()
			if path==None:
				return
			i = path[0]
			if dest is None:
				model.move_after(model.get_iter(i), model.get_iter(len(model)-1))
			elif dest[1] in (gtk.TREE_VIEW_DROP_BEFORE, gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
				model.move_before(model.get_iter(i), model.get_iter(dest[0][0]))
			else:
				model.move_after(model.get_iter(i), model.get_iter(dest[0][0]))
		else:
			smodel = srcTreev.get_model()
			sIter = smodel.get_iter(srcTreev.dragPath)
			row = [smodel.get(sIter, j)[0] for j in range(2)]
			smodel.remove(sIter)
			if dest is None:
				model.append(row)
			elif dest[1] in (gtk.TREE_VIEW_DROP_BEFORE, gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
				model.insert_before(model.get_iter(dest[0]), row)
			else:
				model.insert_after(model.get_iter(dest[0]), row)
	def makeSwin(self):
		swin = gtk.ScrolledWindow()
		swin.add(self)
		swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		swin.set_property('width-request', 200)
		return swin


class ActiveCalsTreeView(AICalsTreeview):
	isActive = True
	title = _('Active')
	dragId = 100

class InactiveCalsTreeView(AICalsTreeview):
	isActive = False
	title = _('Inactive')
	dragId = 101



class AICalsPrefItem():
	def __init__(self):
		self._widget = gtk.HBox()
		size = gtk.ICON_SIZE_SMALL_TOOLBAR
		######
		toolbar = gtk.Toolbar()
		toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
		########
		treev = ActiveCalsTreeView()
		treev.connect('row-activated', self.activeTreevRActivate)
		treev.connect('focus-in-event', self.activeTreevFocus)
		treev.get_selection().connect('changed', self.activeTreevSelectionChanged)
		###
		pack(self._widget, treev.makeSwin())
		####
		self.activeTreev = treev
		self.activeTrees = treev.get_model()
		########
		toolbar = gtk.Toolbar()
		toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
		####
		tb = gtk.ToolButton()
		tb.set_direction(gtk.TEXT_DIR_LTR)
		tb.action = ''
		self.leftRightButton = tb
		set_tooltip(tb, _('Activate/Inactivate'))
		tb.connect('clicked', self.leftRightClicked)
		toolbar.insert(tb, -1)
		####
		tb = toolButtonFromStock(gtk.STOCK_GO_UP, size)
		set_tooltip(tb, _('Move up'))
		tb.connect('clicked', self.upClicked)
		toolbar.insert(tb, -1)
		##
		tb = toolButtonFromStock(gtk.STOCK_GO_DOWN, size)
		set_tooltip(tb, _('Move down'))
		tb.connect('clicked', self.downClicked)
		toolbar.insert(tb, -1)
		##
		pack(self._widget, toolbar)
		########
		treev = InactiveCalsTreeView()
		treev.connect('row-activated', self.inactiveTreevRActivate)
		treev.connect('focus-in-event', self.inactiveTreevFocus)
		treev.get_selection().connect('changed', self.inactiveTreevSelectionChanged)
		###
		pack(self._widget, treev.makeSwin())
		####
		self.inactiveTreev = treev
		self.inactiveTrees = treev.get_model()
		########
	def setLeftRight(self, isRight):
		tb = self.leftRightButton
		if isRight is None:
			tb.set_label_widget(None)
			tb.action = ''
		else:
			tb.set_label_widget(
				gtk.image_new_from_stock(
					gtk.STOCK_GO_FORWARD if isRight ^ rtl else gtk.STOCK_GO_BACK,
					gtk.ICON_SIZE_SMALL_TOOLBAR,
				)
			)
			tb.action = 'inactivate' if isRight else 'activate'
		tb.show_all()
	def activeTreevFocus(self, treev, gevent=None):
		self.setLeftRight(True)
	def inactiveTreevFocus(self, treev, gevent=None):
		self.setLeftRight(False)
	def leftRightClicked(self, obj=None):
		tb = self.leftRightButton
		if tb.action == 'activate':
			path, col = self.inactiveTreev.get_cursor()
			if path:
				self.activateIndex(path[0])
		elif tb.action == 'inactivate':
			if len(self.activeTrees) > 1:
				path, col = self.activeTreev.get_cursor()
				if path:
					self.inactivateIndex(path[0])
	def getCurrentTreeview(self):
		tb = self.leftRightButton
		if tb.action == 'inactivate':
			return self.activeTreev
		elif tb.action == 'activate':
			return self.inactiveTreev
		else:
			return
	def upClicked(self, obj=None):
		treev = self.getCurrentTreeview()
		if not treev:
			return
		path, col = treev.get_cursor()
		if path:
			i = path[0]
			s = treev.get_model()
			if i > 0:
				s.swap(s.get_iter(i-1), s.get_iter(i))
				treev.set_cursor(i-1)
	def downClicked(self, obj=None):
		treev = self.getCurrentTreeview()
		if not treev:
			return
		path, col = treev.get_cursor()
		if path:
			i = path[0]
			s = treev.get_model()
			if i < len(s)-1:
				s.swap(s.get_iter(i), s.get_iter(i+1))
				treev.set_cursor(i+1)
	def inactivateIndex(self, index):
		self.inactiveTrees.prepend(self.activeTrees[index])
		del self.activeTrees[index]
		self.inactiveTreev.set_cursor(0)
		try:
			self.activeTreev.set_cursor(min(index, len(self.activeTrees)-1))
		except:
			pass
		self.inactiveTreev.grab_focus()## FIXME
	def activateIndex(self, index):
		self.activeTrees.append(self.inactiveTrees[index])
		del self.inactiveTrees[index]
		self.activeTreev.set_cursor(len(self.activeTrees)-1)## FIXME
		try:
			self.inactiveTreev.set_cursor(min(index, len(self.inactiveTrees)-1))
		except:
			pass
		self.activeTreev.grab_focus()## FIXME
	def activeTreevSelectionChanged(self, selection):
		if selection.count_selected_rows() > 0:
			self.setLeftRight(True)
		else:
			self.setLeftRight(None)
	def inactiveTreevSelectionChanged(self, selection):
		if selection.count_selected_rows() > 0:
			self.setLeftRight(False)
		else:
			self.setLeftRight(None)
	def activeTreevRActivate(self, treev, path, col):
		self.inactivateIndex(path[0])
	def inactiveTreevRActivate(self, treev, path, col):
		self.activateIndex(path[0])
	def updateVar(self):
		calTypes.activeNames = [row[0] for row in self.activeTrees]
		calTypes.inactiveNames = [row[0] for row in self.inactiveTrees]
		calTypes.update()
	def updateWidget(self):
		self.activeTrees.clear()
		self.inactiveTrees.clear()
		##
		for mode in calTypes.active:
			module = calTypes[mode]
			self.activeTrees.append([module.name, _(module.desc)])
		##
		for mode in calTypes.inactive:
			module = calTypes[mode]
			self.inactiveTrees.append([module.name, _(module.desc)])
	def confStr(self):
		text = ''
		text += 'calTypes.activeNames=%r\n'%calTypes.activeNames
		text += 'calTypes.inactiveNames=%r\n'%calTypes.inactiveNames
		return text



