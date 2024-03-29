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


import sys, os, gettext

import time
from time import localtime
from time import time as now

from os.path import join, isfile, dirname


_mypath = __file__
if _mypath.endswith('.pyc'):
	_mypath = _mypath[:-1]
dataDir = dirname(_mypath) + '/pray_times_files/'
rootDir = '/usr/share/starcal2'

sys.path.insert(0, dataDir)## FIXME
sys.path.insert(0, rootDir)## FIXME

from natz.local import get_localzone

from scal2 import plugin_api as api

from scal2.path import *
from pray_times_backend import PrayTimes

## DO NOT IMPORT core IN PLUGINS
from scal2.time_utils import floatHourToTime
from scal2.locale_man import tr as _
from scal2.plugin_man import BasePlugin
from scal2.cal_types.gregorian import to_jd as gregorian_to_jd
from scal2.time_utils import getUtcOffsetByJd, getUtcOffsetCurrent, getEpochFromJd
from scal2.os_utils import kill, goodkill
from scal2.utils import myRaise
#from scal2 import event_lib## needs core!! FIXME

from threading import Timer

#if 'gtk' in sys.modules:
from pray_times_gtk import *
#else:
#	from pray_times_qt import *

####################################################

confPath = join(plugConfDir, 'pray_times')
localTz = get_localzone()


####################### Methods and Classes ##################

def readLocationData():
	lines = open(dataDir+'/locations.txt').read().split('\n')
	cityData = []
	country = ''
	for l in lines:
		p = l.split('\t')
		if len(p)<2:
			#print(p)
			continue
		if p[0]=='':
			if p[1]=='':
				city, lat, lng = p[2:5]
				#if country=='Iran':
				#	print(city)
				if len(p)>4:
					cityData.append((
						country + '/' + city,
						_(country) + '/' + _(city),
						float(lat),
						float(lng)
					))
				else:
					print(country, p)
			else:
				country = p[1]
	return cityData

def guessLocation(cityData):
	tzname = str(localTz)
	## FIXME
	#for countryCity, countryCityLocale, lat, lng in cityData:
	return 'Tehran', 35.705, 51.4216


'''
event_classes = api.get('event_lib', 'classes')
EventRule = api.get('event_lib', 'EventRule')

@event_classes.rule.register
class PrayTimeEventRule(EventRule):
	plug = None ## FIXME
	name = 'prayTime'
	desc = _('Pray Time')
	provide = ('time',)
	need = ()
	conflict = ('dayTimeRange', 'cycleLen',)
	def __init__(self, parent):
		EventRule.__init__(self, parent)
	def calcOccurrence(self, startEpoch, endEpoch, event):
		self.plug.get_times_jd(jd)
	getInfo = lambda self: self.desc
'''

class TextPlug(BasePlugin, TextPlugUI):
	## all options (except for "enable" and "show_date") will be saved in file confPath
	azanTimeNamesAll = (
		'fajr',
		'dhuhr',
		'asr',
		'maghrib',
		'isha',
	)
	def __init__(self, enable=True, show_date=False):
		#print('----------- praytime TextPlug.__init__')
		#print('From plugin: core.VERSION=%s'%api.get('core', 'VERSION'))
		#print('From plugin: core.aaa=%s'%api.get('core', 'aaa'))
		BasePlugin.__init__(
			self,
			path=_mypath,
			mode='gregorian',
			desc=_('Islamic Pray Times'),
			enable=enable,
			show_date=show_date,
			last_day_merge=False,
		)
		self.external = True
		self.name = _('Islamic Pray Times')
		self.about = _('Islamic Pray Times') ## FIXME
		self.has_config = True
		self.cityData = readLocationData()
		##############
		confNeedsSave = False
		######
		locName, lat, lng = '', 0, 0
		method = ''
		#######
		imsak = 10 ## minutes before Fajr (Morning Azan)
		#asrMode=ASR_STANDARD
		#highLats='NightMiddle'
		#timeFormat='24h'
		shownTimeNames = ('fajr', 'sunrise', 'dhuhr', 'maghrib', 'midnight')
		## FIXME rename shownTimeNames to activeTimeNames
		## or add another list azanSoundTimeNames
		sep = '     '
		##
		azanEnable = False
		azanFile = None
		##
		preAzanEnable = False
		preAzanFile = None
		preAzanMinutes = 2.0
		####
		if isfile(confPath):
			exec(open(confPath).read())
		else:
			confNeedsSave = True
		####
		if not locName:
			confNeedsSave = True
			locName, lat, lng = guessLocation(self.cityData)
			method = 'Tehran'
			## guess method from location FIXME
		#######
		self.locName = locName
		self.imsak = imsak
		self.backend = PrayTimes(lat, lng, methodName=method, imsak='%d min'%imsak)
		self.shownTimeNames = shownTimeNames
		self.sep = sep
		####
		self.azanEnable = azanEnable
		self.azanFile = azanFile
		##
		self.preAzanEnable = preAzanEnable
		self.preAzanFile = preAzanFile
		self.preAzanMinutes = preAzanMinutes
		##
		self.preAzanMinutes = preAzanMinutes
		#######
		#PrayTimeEventRule.plug = self
		#######
		if confNeedsSave:
			self.saveConfig()
		#######
		self.makeWidget()## FIXME
		self.onCurrentDateChange(localtime()[:3])
		###
		#self.doPlayPreAzan()
		#time.sleep(2)
		#self.doPlayAzan() ## for testing ## FIXME
	def saveConfig(self):
		text = ''
		text += 'lat=%r\n'%self.backend.lat
		text += 'lng=%r\n'%self.backend.lng
		text += 'method=%r\n'%self.backend.method.name
		for attr in (
			'locName',
			'shownTimeNames',
			'imsak',
			'sep',
			'azanEnable',
			'azanFile',
			'preAzanEnable',
			'preAzanFile',
			'preAzanMinutes',
		):
			text += '%s=%r\n'%(
				attr,
				getattr(self, attr),
			)
		open(confPath, 'w').write(text)
	#def date_change_after(self, widget, year, month, day):
	#	self.dialog.menuCell.add(self.menuitem)
	#	self.menu_unmap_id = self.dialog.menuCell.connect('unmap', self.menu_unmap)
	#def menu_unmap(self, menu):
	#	menu.remove(self.menuitem)
	#	menu.disconnect(self.menu_unmap_id)
	def get_times_jd(self, jd):
		times = self.backend.getTimesByJd(
			jd,
			getUtcOffsetByJd(jd)/3600.0,
		)
		return [(name, times[name]) for name in self.shownTimeNames]
	def getFormattedTime(self, tm):## tm is float hour
		try:
			h, m, s = floatHourToTime(float(tm))
		except ValueError:
			return tm
		else:
			return '%d:%.2d'%(h, m)
	def get_text_jd(self, jd):
		return self.sep.join([
			'%s: %s'%(_(name.capitalize()), self.getFormattedTime(tm))
			for name, tm in self.get_times_jd(jd)
		])
	def get_text(self, year, month, day):## just for compatibity (usage by external programs)
		return self.get_text_jd(gregorian_to_jd(year, month, day))
	def update_cell(self, c):
		text = self.get_text_jd(c.jd)
		if text!='':
			if c.pluginsText!='':
				c.pluginsText += '\n'
			c.pluginsText += text
	def killPrevSound(self):
		try:
			p = self.proc
		except AttributeError:
			pass
		else:
			print('killing %s'%p.pid)
			goodkill(p.pid, interval=0.01)
			#kill(p.pid, 15)
			#p.terminate()
	def doPlayAzan(self):## , tm
		if not self.azanEnable:
			return
		#dt = tm - now()
		#print('---------------------------- doPlayAzan, dt=%.1f'%dt)
		#if dt > 1:
		#	Timer(
		#		int(dt),
		#		self.doPlayAzan,
		#		#tm,
		#	).start()
		#	return
		self.killPrevSound()
		self.proc = popenFile(self.azanFile)
	def doPlayPreAzan(self):## , tm
		if not self.preAzanEnable:
			return
		#dt = tm - now()
		#print('---------------------------- doPlayPreAzan, dt=%.1f'%dt)
		#if dt > 1:
		#	Timer(
		#		int(dt),
		#		self.doPlayPreAzan,
		#		#tm,
		#	).start()
		#	return
		self.killPrevSound()
		self.proc = popenFile(self.preAzanFile)
	def onCurrentDateChange(self, gdate):
		print 'praytimes: onCurrentDateChange', gdate
		if not self.enable:
			return
		jd = gregorian_to_jd(*tuple(gdate))
		#print(getUtcOffsetByJd(jd)/3600.0, getUtcOffsetCurrent()/3600.0)
		#utcOffset = getUtcOffsetCurrent()
		utcOffset = getUtcOffsetByJd(jd)
		tmUtc = now()
		epochLocal = tmUtc + utcOffset
		secondsFromMidnight = epochLocal % (24*3600)
		midnightUtc = tmUtc - secondsFromMidnight
		#print('------- hours from midnight', secondsFromMidnight/3600.0)
		for timeName, azanHour in self.backend.getTimesByJd(
			jd,
			utcOffset/3600.0,
		).items():
			if timeName not in self.azanTimeNamesAll:
				continue
			if timeName not in self.shownTimeNames:
				continue
			azanSec = azanHour * 3600.0
			#####
			toAzanSecs = int(azanSec - secondsFromMidnight)
			if toAzanSecs >= 0:
				preAzanSec = azanSec - self.preAzanMinutes * 60
				toPreAzanSec = max(
					0,
					int(preAzanSec - secondsFromMidnight)
				)
				print('toPreAzanSec=%.1f'%toPreAzanSec)
				Timer(
					toPreAzanSec,
					self.doPlayPreAzan,
					#midnightUtc + preAzanSec,
				).start()
				###
				print('toAzanSecs=%.1f'%toAzanSecs)
				Timer(
					toAzanSecs,
					self.doPlayAzan,
					#midnightUtc + azanSec,
				).start()



if __name__=='__main__':
	#sys.path.insert(0, '/usr/share/starcal2')
	#from scal2 import core
	#from scal2.locale_man import rtl
	#if rtl:
	#	gtk.widget_set_default_direction(gtk.TEXT_DIR_RTL)
	dialog = LocationDialog(readLocationData())
	dialog.connect('delete-event', gtk.main_quit)
	#dialog.connect('response', gtk.main_quit)
	dialog.resize(600, 600)
	print(dialog.run())
	#gtk.main()




