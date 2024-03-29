#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import event_lib

from scal2.ui_gtk import *
from scal2.ui_gtk.mywidgets.multi_spin.time_b import TimeButton

class WidgetClass(TimeButton):
	def __init__(self, rule):
		self.rule = rule
		TimeButton.__init__(self)
	def updateWidget(self):
		self.set_value(self.rule.dayTime)
	def updateVars(self):
		self.rule.dayTime = self.get_value()


