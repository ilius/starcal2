#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import event_lib

from scal2.ui_gtk import *
from scal2.ui_gtk.mywidgets.num_ranges_entry import NumRangesEntry

class WidgetClass(NumRangesEntry):
	def __init__(self, rule):
		self.rule = rule
		NumRangesEntry.__init__(self, 0, 9999, 10)
	def updateWidget(self):
		self.setValues(self.rule.values)
	def updateVars(self):
		self.rule.values = self.getValues()
	def changeMode(self, mode):
		if mode == self.rule.getMode():
			return
		self.updateVars()
		self.rule.changeMode(mode)
		self.updateWidget()

