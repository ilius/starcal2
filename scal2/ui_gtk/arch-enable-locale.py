#!/usr/bin/env python2
import sys, os, subprocess
from time import time as now

import gtk

localeGen = '/etc/locale.gen'

def error(text, parent=None):
  d = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT,\
	gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, text.strip())
  d.set_title('Error')
  d.run()

def errorExit(text, parent=None):
	error(text, parent)
	sys.exit(1)


if __name__=='__main__':
	if os.getuid()!=0:
		errorExit('This program must be run as root')
	if not os.path.isfile(localeGen):
		errorExit('File "%s" does not exist!'%localeGen)
	localeName = sys.argv[1].lower().replace('.', ' ')
	lines = open(localeGen).read().split('\n')
	for (i, line) in enumerate(lines):
		if line.lower().startswith(localeName):
			print('locale "%s" is already enabled'%localeName)
			break
		if line.lower().startswith('#'+localeName):
			lines[i] = line[1:]
			os.rename(localeGen, '%s.%s'%(localeGen, now()))
			open(localeGen, 'w').write('\n'.join(lines))
			exit_code = subprocess.call('/usr/sbin/locale-gen')
			print('enabling locale "%s" done'%localeName)
			break
	else:
		errorExit('locale "%s" not found!'%localeName)


