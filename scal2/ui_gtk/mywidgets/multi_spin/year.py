from scal2.mywidgets.multi_spin import YearField
from scal2.ui_gtk.mywidgets.multi_spin import SingleSpinButton

class YearSpinButton(SingleSpinButton):
	def __init__(self, **kwargs):
		SingleSpinButton.__init__(
			self,
			YearField(),
			**kwargs
		)

