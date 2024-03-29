from time import localtime

from scal2.mywidgets.multi_spin import YearField, MonthField
from scal2.ui_gtk.mywidgets.multi_spin import MultiSpinButton

class YearMonthButton(MultiSpinButton):
	def __init__(self, date=None, **kwargs):
		MultiSpinButton.__init__(
			self,
			'/',
			(
				YearField(),
				MonthField(),
			),
			**kwargs
		)
		if date==None:
			date = localtime()[:2]
		self.set_value(date)



