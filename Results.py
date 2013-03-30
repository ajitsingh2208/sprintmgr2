import wx
import wx.grid as gridlib

import os
import sys
import TestData
import Model
import Utils
from ReorderableGrid import ReorderableGrid
from Competitions import SetDefaultData
from Utils import WriteCell
from Events import FontSize

class Results(wx.Panel):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self, parent):
		"""Constructor"""
		wx.Panel.__init__(self, parent)
 
		self.font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		
		self.showResultsLabel = wx.StaticText( self, wx.ID_ANY, 'Show Results:' )
		self.showResultsLabel.SetFont( self.font )
		self.showResults = wx.Choice( self, wx.ID_ANY, choices = ['Time Trial'] )
		self.showResults.SetFont( self.font )
		self.showResults.SetSelection( 0 )
		
		self.showResults.Bind( wx.EVT_CHOICE, self.onShowResults )
		self.showNames = wx.ToggleButton( self, wx.ID_ANY, 'Show Names' )
		self.showNames.SetFont( self.font )
		self.showNames.Bind( wx.EVT_TOGGLEBUTTON, self.onToggleShow )
		self.showTeams = wx.ToggleButton( self, wx.ID_ANY, 'Show Teams' )
		self.showTeams.SetFont( self.font )
		self.showTeams.Bind( wx.EVT_TOGGLEBUTTON, self.onToggleShow )
 
		self.headerNames = ['Pos', 'Bib', 'Rider', 'Team', 'License']
		
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.DisableDragRowSize()
		self.grid.SetRowLabelSize( 64 )
		self.grid.CreateGrid( 0, len(self.headerNames) )
		self.grid.SetRowLabelSize( 0 )
		self.grid.EnableReorderRows( False )
		self.setColNames()

		sizer = wx.BoxSizer(wx.VERTICAL)
		
		hs = wx.BoxSizer(wx.HORIZONTAL)
		hs.Add( self.showResultsLabel, 0, flag=wx.ALIGN_CENTRE_VERTICAL, border = 4 )
		hs.Add( self.showResults, 1, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, border = 4 )
		hs.Add( self.showNames, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4 )
		hs.Add( self.showTeams, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 4 )
		
		sizer.Add(hs, 0, flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border = 6 )
		sizer.Add(self.grid, 1, flag=wx.EXPAND|wx.ALL, border = 6)
		self.SetSizer(sizer)
	
	def onToggleShow( self, e ):
		model = Model.model
		model.resultsShowNames = self.showNames.GetValue()
		model.resultsShowTeams = self.showTeams.GetValue()
		self.refresh()
	
	def setColNames( self ):
		self.grid.SetLabelFont( self.font )
		for col, headerName in enumerate(self.headerNames):
			self.grid.SetColLabelValue( col, headerName )
			
			attr = gridlib.GridCellAttr()
			attr.SetFont( self.font )
			if self.headerNames[col] in ('Bib', 'Event'):
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP )
			elif self.headerNames[col] == 'Time':
				attr.SetRenderer( gridlib.GridCellFloatRenderer(-1, 3) )
			elif self.headerNames[col] == 'Pos':
				attr.SetAlignment( wx.ALIGN_RIGHT, wx.ALIGN_TOP )
			elif self.headerNames[col].startswith( '==' ):
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_VERTICAL_CENTRE )
			elif self.headerNames[col].startswith( 'H' ):
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP )
			attr.SetReadOnly( True )
			self.grid.SetColAttr( col, attr )
	
	def fixShowResults( self ):
		model = Model.model
		competition = model.competition
		
		choices = ['Time Trial']
		for tournament in competition.tournaments:
			for system in tournament.systems:
				name = ('%s: ' % tournament.name if tournament.name else '') + system.name
				choices.append( name )
		choices.append( 'Overall' )
		
		self.showResults.SetItems( choices )
		
		if model.showResults >= len(choices):
			model.showResults = 0
		self.showResults.SetSelection( model.showResults )
		
	def getHideCols( self, headerNames ):
		model = Model.model
		toHide = set()
		for col, h in enumerate(headerNames):
			if h == 'Name' and not getattr(model, 'resultsShowNames', True):
				toHide.add( col )
			elif h == 'Team' and not getattr(model, 'resultsShowTeams', True):
				toHide.add( col )
		return toHide
	
	def getGrid( self ):
		return self.grid
		
	def getTitle( self ):
		return self.showResults.GetStringSelection() + ' Results'
	
	def onShowResults( self, event ):
		Model.model.showResults = self.showResults.GetSelection()
		self.refresh()
	
	def refresh( self ):
		self.fixShowResults()
		self.grid.ClearGrid()
		
		model = Model.model
		competition = model.competition
		
		self.showNames.SetValue( getattr(model, 'resultsShowNames', True) )
		self.showTeams.SetValue( getattr(model, 'resultsShowTeams', True) )
		
		resultName = self.showResults.GetStringSelection()
		
		if resultName.startswith( 'Time' ):
			self.headerNames = ['Pos', 'Bib', 'Name', 'Team', 'Time']
			hideCols = self.getHideCols( self.headerNames )
			self.headerNames = [h for c, h in enumerate(self.headerNames) if c not in hideCols]
			
			riders = sorted( model.riders, key = lambda r: r.qualifyingTime )
			Utils.AdjustGridSize( self.grid, rowsRequired = len(riders), colsRequired = len(self.headerNames) )
			self.setColNames()
			starters = competition.starters
			for row, r in enumerate(riders):
				if row < starters:
					pos = str(row + 1)
				else:
					pos = 'DNQ'
					for col in xrange(self.grid.GetNumberCols()):
						self.grid.SetCellBackgroundColour( row, col, wx.Colour(200,200,200) )
						
				writeCell = WriteCell( self.grid, row )
				for col, value in enumerate([pos, str(r.bib), r.full_name, r.team, '%.3f' % r.qualifyingTime]):
					if col not in hideCols:
						writeCell( value )
					
		elif resultName == 'Overall':
			self.headerNames = ['Pos', 'Bib', 'Name', 'Team', 'License']
			hideCols = self.getHideCols( self.headerNames )
			self.headerNames = [h for c, h in enumerate(self.headerNames) if c not in hideCols]
			
			results, dnfs, dqs = competition.getResults()
			Utils.AdjustGridSize( self.grid, rowsRequired = len(results) + len(dnfs) + len(dqs), colsRequired = len(self.headerNames) )
			self.setColNames()
			for row, r in enumerate(results):
				writeCell = WriteCell( self.grid, row )
				if not r:
					for col in xrange(self.grid.GetNumberCols()):
						writeCell( '' )
				else:
					for col, value in enumerate([row+1, r.bib if r.bib else '', r.full_name, r.team, r.license]):
						if col not in hideCols:
							writeCell( str(value) )
			
			row = len(results)
			for r in dnfs:
				writeCell = WriteCell( self.grid, row )
				for col, value in enumerate(['DNF', r.bib, r.full_name, r.team, r.license]):
					if col not in hideCols:
						writeCell( str(value) )
				row += 1
				
			for r in dqs:
				writeCell = WriteCell( self.grid, row )
				for col, value in enumerate(['DQ', r.bib, r.full_name, r.team, r.license]):
					if col not in hideCols:
						writeCell( str(value) )
				row += 1
		else:
			# Find the Tournament and System selected.
			keepGoing = True
			for tournament in competition.tournaments:
				for system in tournament.systems:
					name = ('%s: ' % tournament.name if tournament.name else '') + system.name
					if name == resultName:
						keepGoing = False
						break
				if not keepGoing:
					break
			
			heatsMax = max( event.heatsMax for event in system.events )
			if heatsMax == 1:
				self.headerNames = ['Event','Bib','Name','Team','    ','Pos','Bib','Name','Team','Time']
			else:
				self.headerNames = ['Event','Bib','Name','Team','H1','H2','H3','    ','Pos','Bib','Name','Team','Time']
			hideCols = self.getHideCols( self.headerNames )
			self.headerNames = [h for c, h in enumerate(self.headerNames) if c not in hideCols]
			
			Utils.AdjustGridSize( self.grid, rowsRequired = len(system.events), colsRequired = len(self.headerNames) )
			self.setColNames()
			state = competition.state
			
			for row, event in enumerate(system.events):
				writeCell = WriteCell( self.grid, row )
				
				writeCell( str(row+1) )
				
				riders = [state.labels.get(c, None) for c in event.composition]
				writeCell( '\n'.join([str(rider.bib) if rider else '' for rider in riders]) )
				if getattr(model, 'resultsShowNames', True):
					writeCell( '\n'.join([rider.full_name if rider else '' for rider in riders]) )
				if getattr(model, 'resultsShowTeams', True):
					writeCell( '\n'.join([rider.team if rider else '' for rider in riders]) )

				if heatsMax != 1:
					for heat in xrange(heatsMax):
						if event.heatsMax != 1:
							writeCell( '\n'.join(event.getHeatPlaces(heat+1)) )
						else:
							writeCell( '' )
				
				writeCell( '===>' )
				
				out = [event.winner] + event.others
				riders = [state.labels.get(c, None) for c in out]
				writeCell( '\n'.join( str(i+1) for i in xrange(len(riders))) )
				writeCell( '\n'.join([str(rider.bib if rider.bib else '') if rider else '' for rider in riders]) )
				if getattr(model, 'resultsShowNames', True):
					writeCell( '\n'.join([rider.full_name if rider else '' for rider in riders]) )
				if getattr(model, 'resultsShowTeams', True):
					writeCell( '\n'.join([rider.team if rider else '' for rider in riders]) )
				if event.winner in state.labels:
					try:
						value = '%.3f' % event.starts[-1].times[1]
					except (KeyError, IndexError, ValueError):
						value = ''
					writeCell( value )
		
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		
	def commit( self ):
		pass
		
########################################################################

class ResultsFrame(wx.Frame):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		wx.Frame.__init__(self, None, title="Results Grid Test", size=(800,600) )
		panel = Results(self)
		panel.refresh()
		self.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
	app = wx.App(False)
	SetDefaultData()
	frame = ResultsFrame()
	app.MainLoop()