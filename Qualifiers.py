import wx
import wx.grid as gridlib

import os
import sys
import TestData
import Utils
import Model
from ReorderableGrid import ReorderableGrid
from Events import FontSize

class Qualifiers(wx.Panel):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self, parent):
		"""Constructor"""
		wx.Panel.__init__(self, parent)
 
		font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		self.title = wx.StaticText(self, wx.ID_ANY, "Enter each Rider's Qualifying Time")
		self.title.SetFont( font )
 
		self.headerNames = ['Bib', 'Name', 'Team', 'Time']
		self.iTime = self.headerNames.index( 'Time' )
		
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.DisableDragRowSize()
		self.grid.SetRowLabelSize( 64 )
		self.grid.CreateGrid( 0, len(self.headerNames) )
		self.setColNames()
		self.grid.EnableReorderRows( False )

		# Set specialized editors for appropriate columns.
		self.grid.SetLabelFont( font )
		for col in xrange(self.grid.GetNumberCols()):
			attr = gridlib.GridCellAttr()
			attr.SetFont( font )
			if col == self.grid.GetNumberCols() - 1:
				attr.SetRenderer( gridlib.GridCellFloatRenderer(-1, 3) )
				attr.SetEditor( gridlib.GridCellFloatEditor(-1, 3) )
			else:
				if col == 0:
					attr.SetRenderer( gridlib.GridCellNumberRenderer() )
				attr.SetReadOnly( True )
			self.grid.SetColAttr( col, attr )
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add( self.title, 0, flag=wx.ALL, border = 6 )
		sizer.Add(self.grid, 1, flag=wx.EXPAND|wx.ALL, border = 6)
		self.SetSizer(sizer)
		
	def getGrid( self ):
		return self.grid
		
	def setColNames( self ):
		for col, headerName in enumerate(self.headerNames):
			self.grid.SetColLabelValue( col, headerName )
						
	def setTestData( self ):
		self.grid.ClearGrid()

		testData = TestData.getTestData()
		Utils.AdjustGridSize( self.grid, rowsRequired = len(testData) )
			
		for row, data in enumerate(testData):
			bib = data[0]
			name = data[1] + ' ' + data[2]
			team = data[3]
			time = data[-1]
			for col, d in enumerate([bib, name, team, time]):
				self.grid.SetCellValue( row, col, str(d) )
		
		# Fix up the column and row sizes.
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		
	def refresh( self ):
		model = Model.model
		riders = model.riders
		
		Utils.AdjustGridSize( self.grid, rowsRequired = len(riders) )
		for row, r in enumerate(riders):
			for col, value in enumerate([str(r.bib), r.full_name, r.team, '%.3f' % r.qualifyingTime]):
				self.grid.SetCellValue( row, col, value )
				
		# Fix up the column and row sizes.
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		
		self.Layout()
		self.Refresh()
		
	def commit( self ):
		# The qualifying times can be changed at any time, however, if the competition is underway, the events cannot
		# be adusted.
		model = Model.model
		riders = model.riders
		
		for row in xrange(self.grid.GetNumberRows()):
			try:
				qt = float(self.grid.GetCellValue(row, self.iTime))
			except:
				qt = 60.0
			if riders[row].qualifyingTime != qt:
				riders[row].qualifyingTime = qt
				model.setChanged( True )
			
		if model.canReassignStarters():
			model.setQualifyingTimes()
			Utils.getMainWin().resetEvents()
		
########################################################################

class QualifiersFrame(wx.Frame):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		wx.Frame.__init__(self, None, title="Qualifier Grid Test", size=(800,600) )
		panel = Qualifiers(self)
		panel.setTestData()
		self.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
	app = wx.App(False)
	frame = QualifiersFrame()
	app.MainLoop()