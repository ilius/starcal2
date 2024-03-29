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

from scal2.utils import s_join
from scal2.bin_heap import MaxHeap


ab_overlaps = lambda a0, b0, a1, b1: b0-a0+b1-a1 - abs(a0+b0-a1-b1) > 0.01
md_overlaps = lambda m0, d0, m1, d1: d0+d1 - abs(m0-m1) > 0.01


def simplifyNumList(nums, minCount=3):## nums must be sorted, minCount >= 2
	ranges = []
	tmp = []
	for n in nums:
		if tmp and n - tmp[-1] != 1:
			if len(tmp)>minCount:
				ranges.append((tmp[0], tmp[-1]))
			else:
				ranges += tmp
			tmp = []
		tmp.append(n)
	if tmp:
		if len(tmp)>minCount:
			ranges.append((tmp[0], tmp[-1]))
		else:
			ranges += tmp
	return ranges

def cleanTimeRangeList(lst):
	num = len(lst)
	points = []
	for start, end in lst:
		points += [
			(start, False),
			(end, True),
		]
	lst = []
	points.sort()
	started_pq = MaxHeap()
	for cursor, isEnd in points:
		if isEnd:
			if not started_pq:
				raise RuntimeError('cursor=%s, lastStart=None'%cursor)
			start, tmp = started_pq.pop()
			#print('pop %s'%start)
			if not started_pq:
				lst.append((start, cursor))
		else:
			#print('push %s'%cursor)
			started_pq.push(cursor, None)
	return lst

def intersectionOfTwoIntervalList(*lists):
	listsN = len(lists)
	assert listsN == 2
	points = []
	for lst_index, lst in enumerate(lists):
		lst = cleanTimeRangeList(lst)
		for start, end in lst:
			if end == start:
				points += [
					(start, 0, lst_index),
					(end, 1, lst_index),
				]
			else:
				points += [
					(start, 0, lst_index),
					(end, -1, lst_index),
				]
	points.sort()
	openStartList = [None for i in range(listsN)]
	result = []
	for cursor, ptype, lst_index in points:
		if ptype == 0: ## start
			## start == cursor
			if openStartList[lst_index] is None:
				openStartList[lst_index] = cursor
			else:
				raise RuntimeError('cursor=%s, openStartList[%s]=%s'%(
					cursor,
					lst_index,
					openStartList[lst_index],
				))
		else:## end (closed or open)
			## end == cursor
			if None not in openStartList:
				start = max(openStartList)
				if start > cursor:
					raise RuntimeError('start - cursor = %s'%(start-cursor))
				result.append((start, cursor))
				#if start == cursor:## FIXME
				#	print('start = cursor = %s, ptype=%s'%(start%(24*3600)/3600.0, ptype))
			openStartList[lst_index] = None
	return result


########################################################################

def testCleanTimeRangeList():
	pprint.pprint(cleanTimeRangeList([
		(6, 7),
		(0, 4),
		(1, 5),
		(2, 3),
		(8, 9),
		(7, 8),
		(8.5, 10),
		(11, 11),
		(5.5, 5.5),
	]))

def testIntersection():
	pprint.pprint(intersectionOfTwoIntervalList(
		[(0,1.5), (3,5), (7,9)],
		[(1,3.5), (4,7.5), (8,10)]
	))

def testJdRanges():
	pprint.pprint(JdListOccurrence([1, 3, 4, 5, 7, 9, 10, 11, 12, 13, 14, 18]).calcJdRanges())

def testSimplifyNumList():
	pprint.pprint(simplifyNumList([1, 2, 3, 4, 5, 7, 9, 10, 14, 16, 17, 18, 19, 21, 22, 23, 24]))

def testOverlapsSpeed():
	from random import normalvariate
	from time import time
	N = 2000000
	a0, b0 = -1, 1
	b_mean = 0
	b_sigma = 2
	###
	getRandomPair = lambda: sorted([normalvariate(b_mean, b_sigma) for i in (0, 1)])
	###
	data = []
	for i in range(N):
		a, b = getRandomPair()
		data.append((a, b))
	t0 = time()
	for a, b in data:
		ab_overlaps(a0, b0, a, b)
	print('%.2f'%(time()-t0))

if __name__=='__main__':
	import pprint
	testCleanTimeRangeList()


