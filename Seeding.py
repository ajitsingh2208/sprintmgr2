import wx
import wx.grid as gridlib

import os
import sys
import TestData
from ReorderableGrid import ReorderableGrid
import Model
import Utils
from Events import FontSize

class Seeding(wx.Panel):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self, parent):
		"""Constructor"""
		wx.Panel.__init__(self, parent)
 
		font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		
		self.title = wx.StaticText(self, wx.ID_ANY, "Enter Rider details and set Qualifing Start Order.  To quickly delete a rider, set Bib to 0")
		self.title.SetFont( font )
 
		self.headerNames = ['Bib', 'First Name', 'Last Name', 'Team', 'License']
		
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.DisableDragRowSize()
		self.grid.SetRowLabelSize( 64 )
		self.grid.CreateGrid( 36, len(self.headerNames) )
		self.setColNames()

		# Set specialized editors for appropriate columns.
		self.grid.SetLabelFont( font )
		for col in xrange(self.grid.GetNumberCols()):
			attr = gridlib.GridCellAttr()
			attr.SetFont( font )
			if col == 0:
				attr.SetRenderer( gridlib.GridCellNumberRenderer() )
				attr.SetEditor( gridlib.GridCellNumberEditor() )
			self.grid.SetColAttr( col, attr )
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add( self.title, 0, flag=wx.ALL, border = 6 )
		sizer.Add(self.grid, 1, flag=wx.EXPAND|wx.ALL, border = 6)
		self.SetSizer(sizer)
		
	def setColNames( self ):
		for col, headerName in enumerate(self.headerNames):
			self.grid.SetColLabelValue( col, headerName )
						
	def setTestData( self ):
		self.grid.ClearGrid()
		
		testData = TestData.getTestData()
		for row, data in enumerate(testData):
			for col, d in enumerate(data):
				self.grid.SetCellValue( row, col, str(d) )
		
		# Fix up the column and row sizes.
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		
	def getGrid( self ):
		return self.grid
		
	def refresh( self ):
		riders = Model.model.riders
		for row, r in enumerate(riders):
			for col, value in enumerate([str(r.bib), r.first_name, r.last_name, r.team, r.license]):
				self.grid.SetCellValue( row, col, value )
				
		for row in xrange(len(riders), self.grid.GetNumberRows()):
			for col in xrange(self.grid.GetNumberCols()):
				self.grid.SetCellValue( row, col, '' )
				
		# Fix up the column and row sizes.
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		
		self.Layout()
		self.Refresh()
				
	def commit( self ):
		riders = []
		for row in xrange(self.grid.GetNumberRows()):
			fields = {}
			for col, attr in enumerate(['bib', 'first_name', 'last_name', 'team', 'license']):
				fields[attr] = self.grid.GetCellValue(row, col).strip()
				
			try:
				bib = int(fields['bib'])
			except ValueError:
				continue
				
			if bib:
				fields['bib'] = bib
				riders.append( Model.Rider(**fields) )
		
		model = Model.model
		oldRiders = dict( (r.bib, r) for r in model.riders )
		oldPosition = dict( (r.bib, p) for p, r in enumerate(model.riders) )
		
		# Check for changes to the seeding.
		changed =  (len(riders) != len(model.riders))
		changed |= any( position != oldPosition.get(r.bib, -1) for position, r in enumerate(riders) )
		changed |= any( r.keyDataFields() != oldRiders.get(r.bib, Model.Rider(-1)).keyDataFields() for r in riders )
		if not changed:
			return
		
		model.setChanged( True )
		
		# Update riders if the competition has not yet started.
		if model.canReassignStarters():
			for r in riders:
				try:
					oldRiders[r.bib].copyDataFields( r )
				except KeyError:
					oldRiders[r.bib] = r
			model.riders = [oldRiders[r.bib] for r in riders]
			model.setQualifyingTimes()
			Utils.getMainWin().resetEvents()
			return
		
		if len(riders) != len(model.riders):
			for r in riders:
				if r.bib in oldRiders:
					oldRiders[r.bib].copyDataFields( r )
			Utils.MessageOK( self, 'Cannot Add or Delete Riders after Competition has Started', 'Cannot Add or Delete Riders' )
			self.refresh()
			return
		
		if not all( r.bib in oldRiders for r in riders ):
			for r in riders:
				if r.bib in oldRiders:
					oldRiders[r.bib].copyDataFields( r )
			Utils.MessageOK( self, 'Cannot Change Bib Numbers after Competition has Started', 'Cannot Change Bib Numbers' )
			self.refresh()
			return
		
		# All the bib numbers match - just change the info and update the sequence.
		model.riders = [oldRiders[r.bib].copyDataFields(r) for r in riders]
		
########################################################################

class SeedingFrame(wx.Frame):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		wx.Frame.__init__(self, None, title="Reorder Grid Test", size=(800,600) )
		panel = Seeding(self)
		panel.setTestData()
		self.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
	app = wx.App(False)
	frame = SeedingFrame()
	app.MainLoop()