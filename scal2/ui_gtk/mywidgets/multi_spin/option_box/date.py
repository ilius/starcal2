from time import localtime

from scal2.mywidgets.multi_spin import YearField, MonthField, DayField
from scal2.ui_gtk.mywidgets.multi_spin.option_box import MultiSpinOptionBox

class DateButtonOption(MultiSpinOptionBox):
	def __init__(self, date=None, **kwargs):
		MultiSpinOptionBox.__init__(
			self,
			'/',
			(
				YearField(),
				MonthField(),
				DayField(),
			),
			**kwargs
		)
		if date==None:
			date = localtime()[:3]
		self.set_value(date)
	def setMaxDay(self, _max):
		self.spin.field.children[2].setMax(_max)
		self.spin.update()

