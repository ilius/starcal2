from time import localtime

from scal2.mywidgets.multi_spin import HourField, Z60Field
from scal2.ui_gtk.mywidgets.multi_spin.option_box import MultiSpinOptionBox

class HourMinuteButtonOption(MultiSpinOptionBox):
	def __init__(self, hm=None, **kwargs):
		MultiSpinOptionBox.__init__(
			self,
			':',
			(
				HourField(),
				Z60Field(),
			),
			**kwargs
		)
		if hm==None:
			hm = localtime()[3:5]
		self.set_value(hm)
	get_value = lambda self: MultiSpinOptionBox.get_value(self) + [0]
	def set_value(self, value):
		if isinstance(value, int):
			value = [value, 0]
		else:
			value = value[:2]
		MultiSpinOptionBox.set_value(self, value)

