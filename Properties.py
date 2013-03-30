import wx

import os
import sys
import Model
from FieldDef import FieldDef
from Competitions import SetDefaultData, getCompetitions
from Events import FontSize
import Utils

class Properties(wx.Panel):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self, parent):
		"""Constructor"""
		wx.Panel.__init__(self, parent)
		
		model = Model.model
		
		self.competitionFormat = 0
		competitionChoices = ['%s (%d Starters)' % (c.name, c.starters) for c in getCompetitions()]
		
		font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		
		self.modelFields = [FieldDef(attr = a, data = getattr(model, a))
			for a in ['competition_name', 'date', 'track', 'organizer', 'category', 'chief_official']]
		self.competitionField = FieldDef(attr = 'competitionFormat', choices = competitionChoices)
 
		fs = wx.FlexGridSizer( len(self.modelFields), 2, 4, 4 )
		for f in self.modelFields:
			label, ctrl = f.makeCtrls( self )
			label.SetFont( font )
			ctrl.SetFont( font )
			fs.Add( label, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL )
			fs.Add( ctrl, flag=wx.EXPAND )
			
		label, ctrl = self.competitionField.makeCtrls( self )
		label.SetFont( font )
		ctrl.SetFont( font )
		fs.Add( label, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL )
		fs.Add( ctrl, flag=wx.EXPAND )
		self.competitionFormatCtrl = ctrl
		
		fs.AddGrowableCol( 1, 1 )
		self.refresh()
		
		borderSizer = wx.BoxSizer( wx.VERTICAL )
		borderSizer.Add( fs, flag=wx.ALL|wx.EXPAND, border = 8 )
		self.SetSizer( borderSizer )
		
	def refresh( self ):
		model = Model.model
		for f in self.modelFields:
			f.refresh( model )
		self.competitionFormatCtrl.SetSelection( 0 )
		for i, c in enumerate(getCompetitions()):
			if c.name == model.competition.name:
				self.competitionFormatCtrl.SetSelection( i )
				break
		self.Refresh()

	def commit( self ):
		model = Model.model
		
		for f in self.modelFields:
			model.changed |= f.commit( model )
			
		competition = getCompetitions()[self.competitionFormatCtrl.GetSelection()]
		if competition.name != model.competition.name:
			# Check that changing the competition will screw anything up.
			if model.canReassignStarters():
				model.competition = competition
				model.setQualifyingTimes()
				Utils.getMainWin().resetEvents()
				model.setChanged( True )
			else:
				Utils.MessageOK( self, 'Cannot Change Competition Format after Event has Started', 'Cannot Change Competion Format' )
		
########################################################################

class PropertiesFrame(wx.Frame):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		wx.Frame.__init__(self, None, title="Properties Test", size=(800,600) )
		panel = Properties(self)
		self.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
	app = wx.App(False)
	SetDefaultData()
	frame = PropertiesFrame()
	app.MainLoop()