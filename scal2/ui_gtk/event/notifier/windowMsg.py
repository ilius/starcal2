# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import event_lib
from scal2 import ui

from scal2.ui_gtk import *

class WidgetClass(gtk.Entry):
	def __init__(self, notifier):
		self.notifier = notifier
		gtk.Entry.__init__(self)
	def updateWidget(self):
		self.set_text(self.notifier.extraMessage)
	def updateVars(self):
		self.notifier.extraMessage = self.get_text()

def hideWindow(widget, dialog):
	dialog.hide()
	return True

def notify(notifier, finishFunc):## FIXME
	event = notifier.event
	dialog = gtk.Dialog()
	####
	lines = []
	lines.append(event.getText())
	if notifier.extraMessage:
		lines.append(notifier.extraMessage)
	text = '\n'.join(lines)
	####
	dialog.set_title(event.getText())
	####
	hbox = gtk.HBox(spacing=15)
	hbox.set_border_width(10)
	if event.icon:
		pack(hbox, gtk.image_new_from_file(event.icon))
		dialog.set_icon_from_file(event.icon)
	label = gtk.Label(text)
	label.set_selectable(True)
	pack(hbox, label, 1, 1)
	pack(dialog.vbox, hbox)
	####
	okB = dialog.add_button(gtk.STOCK_OK, 3)
	okB.connect('clicked', hideWindow, dialog)
	if ui.autoLocale:
		okB.set_label(_('_OK'))
		okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON))
	####
	dialog.vbox.show_all()
	dialog.connect('response', lambda w, e: finishFunc())
	dialog.present()

