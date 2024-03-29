#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import event_lib

from scal2.ui_gtk import *
from scal2.ui_gtk.mywidgets.weekday_combo import WeekDayComboBox
from scal2.ui_gtk.mywidgets.month_combo import MonthComboBox

class WidgetClass(gtk.HBox):
	def __init__(self, rule):
		self.rule = rule
		#####
		gtk.HBox.__init__(self)
		###
		combo = gtk.combo_box_new_text()
		for item in rule.wmIndexNames:
			combo.append_text(item)
		pack(self, combo)
		self.nthCombo = combo
		###
		combo = WeekDayComboBox()
		pack(self, combo)
		self.weekDayCombo = combo
		###
		pack(self, gtk.Label(_(' of ')))
		###
		combo = MonthComboBox(True)
		combo.build(rule.getMode())
		pack(self, combo)
		self.monthCombo = combo
	def updateVars(self):
		self.rule.wmIndex = self.nthCombo.get_active()
		self.rule.weekDay = self.weekDayCombo.getValue()
		self.rule.month = self.monthCombo.getValue()
	def updateWidget(self):
		self.nthCombo.set_active(self.rule.wmIndex)
		self.weekDayCombo.setValue(self.rule.weekDay)
		self.monthCombo.setValue(self.rule.month)

	def changeMode(self, mode):
		if mode == self.rule.getMode():
			return
		self.monthCombo.build(mode)
