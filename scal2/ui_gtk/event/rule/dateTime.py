#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import event_lib

from scal2.ui_gtk import *
from scal2.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal2.ui_gtk.mywidgets.multi_spin.time_b import TimeButton


class WidgetClass(gtk.HBox):
	def __init__(self, rule):
		self.rule = rule
		###
		gtk.HBox.__init__(self)
		###
		self.dateInput = DateButton()
		pack(self, self.dateInput)
		###
		pack(self, gtk.Label('   '+_('Time')))
		self.timeInput = TimeButton()
		pack(self, self.timeInput)
	def updateWidget(self):
		self.dateInput.set_value(self.rule.date)
		self.timeInput.set_value(self.rule.time)
	def updateVars(self):
		self.rule.date = self.dateInput.get_value()
		self.rule.time = self.timeInput.get_value()
	def changeMode(self, mode):
		if mode == self.rule.getMode():
			return
		self.updateVars()
		self.rule.changeMode(mode)
		self.updateWidget()
