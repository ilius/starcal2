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
from time import localtime
from time import time as now

import sys, os, subprocess
from subprocess import Popen
from StringIO import StringIO
import os.path
from os.path import join, isfile, isdir
#from pprint import pprint

from natz.local import get_localzone

from scal2.path import *
from scal2.time_utils import *
from scal2.date_utils import *
from scal2.os_utils import *
from scal2.json_utils import *
from scal2.utils import *

from scal2.cal_types import calTypes, DATE_GREG, getSysDate
from scal2 import locale_man
from scal2.locale_man import tr as _
from scal2.plugin_man import *



try:
	__file__
except NameError:
	import inspect, scal2
	__file__ = join(os.path.dirname(inspect.getfile(scal2)), 'core.py')


VERSION = '2.4.6'
BRANCH = join(rootDir, 'branch')
APP_NAME = 'starcal2'
APP_DESC = 'StarCalendar'
COMMAND = 'starcal2'
homePage = 'http://ilius.github.io/starcal/'
osName = getOsName()
userDisplayName = getUserDisplayName()
#print('--------- Hello %s'%userDisplayName)

localTz = get_localzone()

#print('__file__ = %r'%__file__)
#print('__name__ = %r'%__name__)
#print('__package__ = %r'%__package__)
#print('__builtins__',)
#pprint(__builtins__)
#print
#print('core.dir:')
#pprint(dir())

#print('sys.modules =',)
#pprint(sys.modules)

#__plugin_api_get__ = [
#	'VERSION', 'APP_NAME', 'APP_DESC', 'COMMAND', 'homePage', 'osName', 'userDisplayName'
#	'jd_to_primary', 'primary_to_jd',
#]
#__plugin_api_set__ = []

#def pluginCanGet(funcClass):
#	global __plugin_api_get__
#	__plugin_api_get__.append(funcClass.__name__)
#	return funcClass

#def pluginCanSet(funcClass):
#	global __plugin_api_set__
#	__plugin_api_set__.append(funcClass.__name__)

################################################################################
if os.path.exists(confDir):
	if not isdir(confDir):
		os.rename(confDir, confDir+'-old')
		os.mkdir(confDir)
		os.rename(confDir+'-old', confPath)
else:
	os.mkdir(confDir)

makeDir(plugConfDir)
makeDir(join(confDir, 'log'))
################################################################################

try:
	import logging
	import logging.config

	logConfText = open(join(rootDir, 'conf', 'logging-user.conf')).read()
	for varName in ('confDir',):
		logConfText = logConfText.replace(varName, eval(varName))

	logging.config.fileConfig(StringIO(logConfText))
	log = logging.getLogger(APP_NAME)
except:
	from scal2.utils import FallbackLogger
	log = FallbackLogger()

def myRaise(File=None):
	i = sys.exc_info()
	typ, value, tback = sys.exc_info()
	text = 'line %s: %s: %s\n'%(tback.tb_lineno, typ.__name__, value)
	if File:
		text = 'File "%s", '%File + text
	log.error(text)


################################################################################
####################### class and function defenitions #########################
################################################################################


popen_output = lambda cmd: Popen(cmd, stdout=subprocess.PIPE).communicate()[0]

primary_to_jd = lambda y, m, d: calTypes.primaryModule().to_jd(y, m, d)
jd_to_primary = lambda jd: calTypes.primaryModule().jd_to(jd)

def getCurrentJd():## time.time() and mktime(localtime()) both return GMT, not local
	y, m, d = localtime()[:3]
	return calTypes[DATE_GREG].to_jd(y, m, d)

def getWeekDateHmsFromEpoch(epoch):
   jd, hour, minute, sec = getJhmsFromEpoch(epoch)
   absWeekNumber, weekDay = getWeekDateFromJd(jd)
   return (absWeekNumber, weekDay, hour, minute, sec)

def getMonthWeekNth(jd, mode):
	year, month, day = calTypes[mode].jd_to(jd)
	absWeekNumber, weekDay = getWeekDateFromJd(jd)
	##
	dayDiv, dayMode = divmod(day-1, 7)
	return month, dayDiv, weekDay


getWeekDay = lambda y, m, d: jwday(primary_to_jd(y, m, d)-firstWeekDay)

getWeekDayN = lambda i: weekDayName[(i+firstWeekDay)%7]
## 0 <= i < 7    (0 = first day)
def getWeekDayAuto(i, abr=False):
	if abr:
		return weekDayNameAb[(i+firstWeekDay)%7]
	else:
		return weekDayName[(i+firstWeekDay)%7]

weekDayNameAuto = lambda abr: weekDayNameAb if abr else weekDayName

def getLocaleFirstWeekDay():
	#log.debug('first_weekday', popen_output(['locale', 'first_weekday']))
	return int(popen_output(['locale', 'first_weekday']))-1
	#return int(popen_output('LANG=%s locale first_weekday'%locale_man.lang))-1
	##retrun int(trans('calendar:week_start:0').split(':')[-1])
	## "trans" must read from gtk-2.0.mo !!


## week number in year
def getWeekNumberByJdAndDate(jd, year, month, day):
	if primary_to_jd(year+1, 1, 1) - jd < 7:## FIXME
		if getWeekNumber(*jd_to_primary(jd+14)) == 3:
			return 1
	###
	absWeekNum, weekDay = getWeekDateFromJd(jd)
	ystartAbsWeekNum, ystartWeekDay = getWeekDateFromJd(primary_to_jd(year, 1, 1))
	weekNum = absWeekNum - ystartAbsWeekNum + 1
	###
	if weekNumberMode < 7:
		if ystartWeekDay > (weekNumberMode-firstWeekDay)%7:
			weekNum -= 1
			if weekNum==0:
				weekNum = getWeekNumber(*jd_to_primary(jd-7)) + 1
	###
	return weekNum

def getWeekNumber(year, month, day):
	jd = primary_to_jd(year, month, day)
	return getWeekNumberByJdAndDate(jd, year, month, day)

def getWeekNumberByJd(jd):
	year, month, day = jd_to_primary(jd)
	return getWeekNumberByJdAndDate(jd, year, month, day)

#getYearWeeksCount = lambda year: getWeekNumberByJd(primary_to_jd(year+1, 1, 1)-7)
## FIXME

def getJdFromWeek(year, weekNumber):## FIXME
	## weekDay == 0
	wd0 = getWeekDay(year, 1, 1) - 1
	wn0 = getWeekNumber(year, 1, 1, False)
	jd0 = primary_to_jd(year, 1, 1)
	return jd0 - wd0 + (weekNumber-wn0)*7


getWeekDateFromJd = lambda jd: divmod(jd - firstWeekDay + 1, 7)
## return (absWeekNumber, weekDay)

getAbsWeekNumberFromJd = lambda jd: getWeekDateFromJd(jd)[0]

getStartJdOfAbsWeekNumber = lambda absWeekNumber: absWeekNumber*7 + firstWeekDay - 1


#def getLocaleWeekNumberMode():##????????????
#	return (int(popen_output(['locale', 'week-1stweek']))-1)%8
	## will be 7 for farsi (OK)
	## will be 6 for english (usa) (NOT OK, must be 4)
	#return int(popen_output('LANG=%s locale first_weekday'%locale_man.lang))-1
	## locale week-1stweek:
	##	en_US.UTF-8             7
	##	en_GB.UTF-8             4
	##	fa_IR.UTF-8             0


######################################################

def validatePlugList():
	global allPlugList, plugIndex
	n = len(allPlugList)
	i = 0
	while i<n:
		if allPlugList[i]==None:
			allPlugList.pop(i)
			n -= 1
			try:
				plugIndex.remove(i)
			except ValueError:
				pass
		else:
			i += 1
	#####
	n = len(allPlugList)
	m = len(plugIndex)
	i = 0
	while i<m:
		if plugIndex[i]<n:
			i += 1
		else:
			plugIndex.pop(i)
			m -= 1

def initPlugins():
	#log.debug('----------------------- initPlugins')
	global allPlugList, plugIndex
	#exec(open(userPlugConf).read())## FIXME
	## Assert that user configuarion for plugins is OK
	validatePlugList()
	########################
	names = [os.path.split(plug.path)[1] for plug in allPlugList]
	##newPlugs = []#????????
	for direc in (plugDir, plugDirUser):
		if not isdir(direc):
			continue
		for fname in os.listdir(direc):
			if fname=='__init__.py' or fname in names:##??????????
				continue
			path = '%s/%s'%(direc, fname)
			name = os.path.splitext(fname)[0]
			#if path in path:# The plugin is not new, currently exists in allPlugList
				#log.warning('plugin "%s" already exists.'%path)
				#continue
			if not isfile(path):
				continue
			plug = loadPlugin(path)
			if plug==None:
				continue
			#try:
			plugIndex.append(len(allPlugList))
			allPlugList.append(plug)
			#except:
			#	myRaise(__file__)
	## Assert again that final plugins are OK
	validatePlugList()
	updatePlugins()

def getHolidayPlugins():
	hPlugs = []
	for i in plugIndex:
		plug = allPlugList[i]
		if hasattr(plug, 'holidays'):
			hPlugs.append(plug)
	return hPlugs


def updatePlugins():
	for i in plugIndex:
		plug = allPlugList[i]
		if plug.enable:
			plug.load()
		else:
			plug.clear()


def getPluginsTable():
	## returns a list of [i, enable, show_date, description]
	table = []
	for i in plugIndex:
		plug = allPlugList[i]
		table.append([i, plug.enable, plug.show_date, plug.desc])
	return table


def getDeletedPluginsTable():## returns a list of (i, description)
	table = []
	for i, plug in enumerate(allPlugList):
		try:
			plugIndex.index(i)
		except ValueError:
			table.append((i, plug.desc))
	return table

getAllPlugListRepr = lambda: '[\n' + '\n'.join(['  %r,'%plug for plug in allPlugList]) + '\n]'

def convertAllPluginsToIcs(startYear, endYear):
	startJd = calTypes[DATE_GREG].to_jd(startYear, 1, 1)
	endJd = calTypes[DATE_GREG].to_jd(endYear+1, 1, 1)
	namePostfix = '-%d-%d'%(startYear, endYear)
	for plug in core.allPlugList:
		if isinstance(plug, HolidayPlugin):
			convertHolidayPlugToIcs(plug, startJd, endJd, namePostfix)
		elif isinstance(plug, BuiltinTextPlugin):
			convertBuiltinTextPlugToIcs(plug, startJd, endJd, namePostfix)
		else:
			print('Ignoring unsupported plugin %s'%plug.path)

#########################################################

def restart():## will not return from function
	os.environ['LANG'] = locale_man.sysLangDefault
	restartLow()

#########################################################

def mylocaltime(sec=None, mode=None):
	from scal2.cal_types import convert
	if mode==None:##DATE_GREG
		return list(localtime(sec))
	t = list(localtime(sec))
	t[:3] = convert(t[0], t[1], t[2], DATE_GREG, mode)
	return t


def compressLongInt(num):
	from struct import pack
	return pack('L', num % 2**64).\
	rstrip('\x00').\
	encode('base64')[:-3].\
	replace('/', '_')

getCompactTime = lambda maxDays=1000, minSec=0.1:\
	compressLongInt(
		long(
			now()%(maxDays*24*3600) / minSec
		)
	)

def floatJdEncode(jd, mode):
	jd, hour, minute, second = getJhmsFromEpoch(getEpochFromJd(jd))
	return dateEncode(calTypes[mode].jd_to(jd)) + ' ' + timeEncode((hour, minute, second))

def epochDateTimeEncode(epoch):
	jd, hour, minute, sec = getJhmsFromEpoch(epoch)
	return dateEncode(jd_to_primary(jd)) + ', ' + timeEncode((hour, minute, sec))


def fixStrForFileName(fname):
	fname = fname.replace('/', '_').replace('\\', '_')
	#if osName=='win':## FIXME
	return fname


def openUrl(url):
	if osName=='win':
		return Popen([url])
	if osName=='mac':
		return Popen(['open', url])
	try:
		Popen(['xdg-open', url])
	except:
		myRaise()
	else:
		return
	#if not url.startswith('http'):## FIXME
	#	return
	try:
		import webbrowser
		return webbrowser.open(url)
	except ImportError:
		pass
	try:
		import gnomevfs
		return gnomevfs.url_show(url)
	except ImportError:
		pass
	for command in ('gnome-www-browser', 'firefox', 'iceweasel', 'konqueror'):
		try:
			Popen([command, url])
		except:
			pass
		else:
			return

def stopRunningThreads():
	## Stopping running timer threads
	import threading
	for thread in threading.enumerate():
		#if thread.__class__.__name__ == '_Timer':
		try:
			cancel = thread.cancel
		except AttributeError:
			pass
		else:
			print('stopping thread %s'%thread.getName())
			cancel()


dataToJson =  lambda data: dataToCompactJson(data, useAsciiJson) if useCompactJson \
	else dataToPrettyJson(data, useAsciiJson)

def init():
	initPlugins()

################################################################################
#################### End of class and function defenitions #####################
################################################################################

if len(sys.argv)>1:
	if sys.argv[1] in ('--help', '-h'):
		print('No help implemented yet!')
		sys.exit(0)
	elif sys.argv[1]=='--version':
		print(VERSION)
		sys.exit(0)


#holidayWeekDay=6 ## 6 means last day of week ( 0 means first day of week)
#thDay = (tr('First day'), tr('2nd day'), tr('3rd day'), tr('4th day'),\
#	tr('5th day'), tr('6th day'), tr('Last day'))
#holidayWeekEnable = True

libDir = join(rootDir, 'lib')
if isdir(libDir):
	sys.path.insert(libDir)
	pyVersion = '%d.%d'%tuple(sys.version_info[:2])
	pyLibDir = join(libDir, pyVersion)
	if isdir(pyLibDir):
		sys.path.insert(0, pyLibDir)
	del pyVersion, pyLibDir


################################################################################
###################### Default Configuration ###################################
allPlugList = []
plugIndex = []

holidayWeekDays = [0] ## 0 means Sunday (5 means Friday)
## [5] or [4,5] in Iran
## [0] in most of contries
firstWeekDayAuto = True
firstWeekDay = 0 ## 0 means Sunday (6 means Saturday)
weekNumberModeAuto = False #????????????
weekNumberMode = 7

# 0: First week contains first Sunday of year
# 4: First week contains first Thursday of year (ISO 8601, Gnome Clock)
# 6: First week contains first Saturday of year
# 7: First week contains first day of year
# 8: as Locale
## 1971(53), 1972(52), 1977, 1982, 1983, 1988, 1993, 1994
## 1999(53),2000(52),2005(53),2010(53),2011(52),2016(53),2021,2022,2027,2028
################################################################################
################################################################################
debugMode = False
useCompactJson = False ## FIXME
useAsciiJson = False
eventTextSep = ': ' ## use to seperate summary from description for display
eventTrashLastTop = True


#confPathDef = '/etc/%s/core.conf'%APP_NAME ## ????????????????????????
#if isfile(confPathDef):## ????????????????????????
#	try:
#		exec(open(confPathDef).read())
#		#execfile(confPathDef)
#	except:
#		myRaise(__file__)

################################################################################
#################### Loading user core configuration ###########################


sysConfPath = join(sysConfDir, 'core.conf')
if isfile(sysConfPath):
	try:
		exec(open(sysConfPath).read())
	except:
		myRaise(__file__)

confPath = join(confDir, 'core.conf')
if isfile(confPath):
	try:
		exec(open(confPath).read())
	except:
		myRaise(__file__)


################################################################################

try:
	version
except NameError:
	prefVersion = ''
else:
	prefVersion = version
	del version

prefIsOlderThan = lambda v: versionLessThan(prefVersion, v)

try:## just for compatibility
	calTypes.activeNames = activeCalNames
except NameError:
	pass

calTypes.update()

#########################################

licenseText = _('licenseText')
if licenseText in ('licenseText', ''):
	licenseText = open('%s/license-dialog'%rootDir).read()

aboutText = _('aboutText')
if aboutText in ('aboutText', ''):
	aboutText = open('%s/about'%rootDir).read()


weekDayName = (
	_('Sunday'),
	_('Monday'),
	_('Tuesday'),
	_('Wednesday'),
	_('Thursday'),
	_('Friday'),
	_('Saturday'),
)
weekDayNameAb = (
	_('Sun'),
	_('Mon'),
	_('Tue'),
	_('Wed'),
	_('Thu'),
	_('Fri'),
	_('Sat'),
)



#if firstWeekDayAuto and os.sep=='/':## only if unix
#	firstWeekDay = getLocaleFirstWeekDay()

#if weekNumberModeAuto and os.sep=='/':## FIXME
#	weekNumberMode = getLocaleWeekNumberMode()

