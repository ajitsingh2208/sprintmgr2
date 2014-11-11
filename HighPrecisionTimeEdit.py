
import wx
import wx.lib.masked             as  masked
import math
import Utils

class HighPrecisionTimeEdit( masked.TextCtrl ):
	defaultValue = '00:00:00.000'
	emptyValue   = '  :  :  .   '

	def __init__( self, parent, id = wx.ID_ANY, seconds = None, allow_none = False, style = 0 ):
		self.allow_none = allow_none
		masked.TextCtrl.__init__(
					self, parent, id,
					style		 = style,
					mask		 = '##:##:##.###',
					defaultValue = '00:00:00.000',
					validRegex   = '[0-9][0-9]:[0-5][0-9]:[0-5][0-9]\.[0-9][0-9][0-9]',
					useFixedWidthFont = False,
				)
		
		if seconds is not None:
			self.SetSeconds( seconds )
									
	def GetSeconds( self ):
		v = self.GetValue()
		if self.allow_none and v == self.emptyValue:
			return None
		else:
			return Utils.StrToSeconds(v)
		
	def SetSeconds( self, secs ):
		if secs is None and self.allow_none:
			masked.TextCtrl.SetValue( self, self.emptyValue )
		else:
			masked.TextCtrl.SetValue( self, Utils.SecondsToStr(secs, True) )

