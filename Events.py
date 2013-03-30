import wx
import wx.grid as gridlib

import os
import sys
import Model
import Utils
from ReorderableGrid import ReorderableGrid, GridCellMultiLineStringRenderer
from roundbutton import RoundButton
from Competitions import SetDefaultData

RoundButtonSize = 72

RoundButtonColor = wx.Colour(0,128,0)
RoundButtonRestartColor = wx.Colour(100,100,0)
RoundButtonCancelColor = wx.Colour(100, 0, 0)

isOK, isSelect, isCancel, isRestart = range(4)
buttonColors = [RoundButtonColor, RoundButtonColor, RoundButtonCancelColor, RoundButtonRestartColor]

FontSize = 24

ActiveBackgroundColour = wx.Colour( 170, 255, 170 )
InactiveBackgroundColour = wx.Colour( 200, 200, 200 )

def MakeRoundButton( parent, label, bType = 0 ):
	btn = RoundButton( parent, wx.ID_ANY, label, size=(RoundButtonSize, RoundButtonSize) )
	btn.SetBackgroundColour( wx.WHITE )
	btn.SetForegroundColour( buttonColors[bType] )
	btn.SetFontToFitLabel()
	return btn

def EnableRoundButton( btn, enable, bType = 0 ):
	if enable:
		btn.SetForegroundColour( buttonColors[bType] )
	else:
		btn.SetForegroundColour( InactiveBackgroundColour )
		
	btn.Enable( enable )
	return btn
	
def visitComponentTree( parent ):
	yield parent
	if hasattr(parent,"Children"):
		for child in parent.Children:
			yield visitComponentTree(child)

#------------------------------------------------------------------------------------

class RestartDialog( wx.Dialog ):
	def __init__( self, parent, id = wx.ID_ANY ):
		wx.Dialog.__init__( self, parent, id, "Restart",
						style=wx.DEFAULT_DIALOG_STYLE|wx.THICK_FRAME|wx.TAB_TRAVERSAL )
						
		font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		
		sizer = wx.BoxSizer( wx.VERTICAL )
		
		self.SetBackgroundColour( wx.WHITE )
		
		bitmap = wx.Bitmap( os.path.join(Utils.getImageFolder(), 'refresh.png'), wx.BITMAP_TYPE_PNG )
		restartBitmap = wx.StaticBitmap( self, wx.ID_ANY, bitmap )
		
		title = wx.StaticText( self, wx.ID_ANY, 'Restart Status Changes' )
		title.SetFont( font )
		self.titleText = title
		
		hsTitle = wx.BoxSizer( wx.HORIZONTAL )
		hsTitle.Add( restartBitmap, 0, flag=wx.EXPAND|wx.ALL, border = 4 )
		hsTitle.Add( title, 0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 4 )
		
		sizer.Add( hsTitle, flag=wx.EXPAND )
		
		self.headerNames = ['Bib', 'Name', 'Team', 'Status    ']
		self.iColStatus = len(self.headerNames) - 1
		
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.EnableReorderRows( False )
		self.grid.SetRowLabelSize( 0 )
		self.grid.CreateGrid( 0, len(self.headerNames) )
		
		sizer.Add( self.grid, 1, flag=wx.ALL|wx.EXPAND, border = 4 )
		
		hs = wx.BoxSizer( wx.HORIZONTAL )	
		self.okButton = MakeRoundButton( self, 'OK' )
		self.cancelButton = MakeRoundButton( self, 'Cancel', isCancel )
		hs.Add( self.cancelButton, flag=wx.ALL, border = 4 )
		hs.AddStretchSpacer()
		hs.Add( self.okButton, flag=wx.ALL, border = 4 )
		
		self.okButton.Bind( wx.EVT_BUTTON, self.onOK )
		self.cancelButton.Bind( wx.EVT_BUTTON, self.onCancel )
		
		sizer.Add( hs, 0, flag=wx.EXPAND )
		
		self.SetSizer( sizer )

	def refresh( self, event ):
		self.event = event
		
		start = event.starts[-1]
		state = event.competition.state
		
		font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		
		startPositions = start.startPositions
		Utils.AdjustGridSize( self.grid, rowsRequired = len(startPositions) )
		
		self.grid.SetLabelFont( font )
		for col in xrange(self.grid.GetNumberCols()):
			self.grid.SetColLabelValue( col, self.headerNames[col] )
			attr = gridlib.GridCellAttr()
			attr.SetFont( font )
			if self.headerNames[col] == 'Bib':
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP );
				attr.SetReadOnly( True )
			elif col == 1 or col == 2:
				attr.SetReadOnly( True )
			elif self.headerNames[col].startswith('Status'):
				if len(start.getRemainingComposition()) > 2:
					choices = ['Rel', 'DQ', 'DNF', '']
					self.titleText.SetLabel( 'Restart Status Change' )
				else:
					choices = ['Inside', '']
					self.titleText.SetLabel( 'Restart Position Change' )
				attr.SetEditor( gridlib.GridCellChoiceEditor(choices = choices) )
			self.grid.SetColAttr( col, attr )
		
		for row, p in enumerate(startPositions):
			rider = state.labels[p]
			self.grid.SetCellValue( row, 0, str(rider.bib) )
			self.grid.SetCellValue( row, 1, rider.full_name )
			self.grid.SetCellValue( row, 2, rider.team )
			self.grid.SetCellValue( row, 3, '' )
		
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		
		self.GetSizer().Layout()
		self.GetSizer().Fit( self )
				
		self.CentreOnParent(wx.BOTH)
		self.SetFocus()

		
	def commit( self ):
		places = []
		for row in xrange(self.grid.GetNumberRows()):
			bib = self.grid.GetCellValue( row, 0 )
			status = self.grid.GetCellValue( row, self.iColStatus )
			places.append( (bib, status) )
		
		start = self.event.starts[-1]
		start.setPlaces( places )
		start.restartRequired = True
		self.event.propagate()
		Model.model.competition.propagate()
		Model.model.setChanged( True )
		Utils.setTitle()
		
	def onOK( self, event ):
		self.commit()
		self.EndModal( wx.ID_OK )
		
	def onCancel( self, event ):
		self.EndModal( wx.ID_CANCEL )

#------------------------------------------------------------------------------------

			
class EnablePanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		
	def SetEnable( self, enable ):
		for c in visitComponentTree(self):
			try:
				self.Enable( enable )
			except:
				pass
		
class EventSelect(EnablePanel):
	def __init__(self, parent):
		EnablePanel.__init__(self, parent)
		self.box = wx.StaticBox( self, wx.ID_ANY, 'Available Events' )
		boxSizer = wx.StaticBoxSizer( self.box, wx.HORIZONTAL )
		
		self.SetBackgroundColour( wx.WHITE )
		
		self.events = []
		self.event = None
		
		self.headerNames = ['Event', 'Bib', 'Name', 'Team', 'In', 'Out']
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.CreateGrid( 0, len(self.headerNames) )
		self.grid.EnableReorderRows( False )
		self.grid.SetRowLabelSize( 40 )
		self.grid.SetSelectionMode( wx.grid.Grid.SelectRows  )
		
		font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		self.grid.SetLabelFont( font )
		for col in xrange(self.grid.GetNumberCols()):
			self.grid.SetColLabelValue( col, self.headerNames[col] )
			attr = gridlib.GridCellAttr()
			attr.SetFont( font )
			attr.SetRenderer( GridCellMultiLineStringRenderer() )
			attr.SetReadOnly( True )
			if self.headerNames[col] == 'Bib':
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP )
			self.grid.SetColAttr( col, attr )
		
		boxSizer.Add( self.grid, 1, flag=wx.ALL|wx.EXPAND, border = 4 )
		
		vs = wx.BoxSizer( wx.VERTICAL )	
		self.selectButton = MakeRoundButton( self, 'Select', isSelect )
		vs.AddSpacer( int(self.grid.GetColLabelSize() + FontSize*1.15 - RoundButtonSize/2) )
		vs.Add( self.selectButton, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM, border = 4 )
		boxSizer.Add( vs, 0, flag=wx.ALL, border = 4 )
		
		self.activeBar = wx.StaticText( self, wx.ID_ANY, '', size=(40, 0) )
		boxSizer.Add( self.activeBar, 0, flag=wx.ALL|wx.EXPAND, border = 4 )
		
		sizer = wx.BoxSizer( wx.VERTICAL )
		sizer.Add( boxSizer, 1, flag=wx.EXPAND )
		self.SetSizer( sizer )
		
	def SetEnable( self, enable ):
		EnablePanel.SetEnable( self, enable )
		for b, t in [(self.selectButton, isSelect)]:
			EnableRoundButton( b, enable, t )
		self.activeBar.SetBackgroundColour( wx.Colour(0, 128, 0) if enable else wx.WHITE )
		self.Refresh()
		
	def refresh( self ):
		self.grid.ClearGrid()
		model = Model.model
		if not model:
			return
			
		self.events = [e for t, s, e in model.competition.getCanStart()]
		self.events.sort( key = lambda e: (0 if e == self.event else 1, e.tournament.i, e.system.i, e.getHeat(), e.i) )
			
		Utils.AdjustGridSize( self.grid, rowsRequired = len(self.events) )
		for row, e in enumerate(self.events):
			self.grid.SetCellValue( row, 0, e.multi_line_name )
			self.grid.SetCellValue( row, 1, e.multi_line_bibs )
			self.grid.SetCellValue( row, 2, e.multi_line_rider_names )
			self.grid.SetCellValue( row, 3, e.multi_line_rider_teams )
			self.grid.SetCellValue( row, 4, e.multi_line_inlabels )
			self.grid.SetCellValue( row, 5, e.multi_line_outlabels )
			if e.system != self.events[0].system:
				for col in xrange(self.grid.GetNumberCols()):
					self.grid.SetCellBackgroundColour( row, col, InactiveBackgroundColour )
			else:
				for col in xrange(self.grid.GetNumberCols()):
					self.grid.SetCellBackgroundColour( row, col, wx.WHITE )

		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		
		if self.events:
			self.grid.SelectRow( 0 )

class EventPosition(EnablePanel):
	def __init__(self, parent):
		EnablePanel.__init__(self, parent)
		self.box = wx.StaticBox( self, wx.ID_ANY, 'Start Positions' )
		boxSizer = wx.StaticBoxSizer( self.box, wx.HORIZONTAL )
		
		self.SetBackgroundColour( wx.WHITE )
		
		self.event = None
		
		self.headerNames = ['Bib', 'Name', 'Team']
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.CreateGrid( 4, len(self.headerNames) )
		
		font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		self.grid.SetLabelFont( font )
		for col in xrange(self.grid.GetNumberCols()):
			self.grid.SetColLabelValue( col, self.headerNames[col] )
			self.grid.SetCellValue( 0, col, self.headerNames[col] )		# Add the label as data.
			attr = gridlib.GridCellAttr()
			attr.SetFont( font )
			attr.SetReadOnly( True )
			if self.headerNames[col] == 'Bib':
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP );
			self.grid.SetColAttr( col, attr )
		
		self.grid.AutoSizeColumns( False )								# Resize to fit the column name.
		self.grid.AutoSizeRows( False )
		for col in xrange(self.grid.GetNumberCols()):
			self.grid.SetCellValue( 0, col, '' )						# Remove the labels.
		
		boxSizer.Add( self.grid, 1, flag=wx.ALL|wx.EXPAND, border = 4 )
		
		self.drawLotsBitmap = wx.Bitmap( os.path.join(Utils.getImageFolder(), 'dice.png'), wx.BITMAP_TYPE_PNG )
		self.drawLotsGreyBitmap = wx.Bitmap( os.path.join(Utils.getImageFolder(), 'dice_grey.png'), wx.BITMAP_TYPE_PNG )
		self.emptyBitmap = wx.EmptyBitmap( self.drawLotsBitmap.GetWidth(), self.drawLotsBitmap.GetHeight(), self.drawLotsBitmap.GetDepth() )
		
		dc = wx.MemoryDC()
		dc.SelectObject(self.emptyBitmap)
		dc.SetBrush( wx.WHITE_BRUSH )
		dc.Clear()
		dc.SelectObject(wx.NullBitmap)
		
		self.drawLotsDisplay = wx.StaticBitmap( self, wx.ID_ANY, self.drawLotsBitmap )
		boxSizer.Add( self.drawLotsDisplay, 0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 4 )
		
		vs = wx.BoxSizer( wx.VERTICAL )
		self.startButton = MakeRoundButton( self, 'Start' )
		self.cancelButton = MakeRoundButton( self, 'Cancel', isCancel )
		vs.Add( self.startButton, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM, border = 4 )
		vs.Add( self.cancelButton, flag=wx.ALL, border = 4 )
		boxSizer.Add( vs, 0, flag=wx.ALL, border = 4 )

		self.activeBar = wx.StaticText( self, wx.ID_ANY, '', size=(40, 0) )
		boxSizer.Add( self.activeBar, 0, flag=wx.ALL|wx.EXPAND, border = 4 )
		
		sizer = wx.BoxSizer( wx.VERTICAL )
		sizer.Add( boxSizer, 1, flag=wx.EXPAND )
		self.SetSizer( sizer )
	
	def SetEnable( self, enable ):
		EnablePanel.SetEnable( self, enable )
		for b, t in [(self.startButton, isSelect), (self.cancelButton, isCancel)]:
			EnableRoundButton( b, enable, t )
		self.activeBar.SetBackgroundColour( wx.Colour(0, 128, 0) if enable else wx.WHITE )
		self.Refresh()
		
	def setEvent( self, event ):
		self.event = event
	
	def refresh( self ):
		if not self.event:
			self.grid.ClearGrid()
			self.drawLotsDisplay.SetBitmap( self.emptyBitmap )
			return
		
		start = self.event.starts[-1]
		if self.startButton.IsEnabled():
			self.drawLotsDisplay.SetBitmap( self.drawLotsBitmap if start.canDrawLots else self.emptyBitmap )
		else:
			self.drawLotsDisplay.SetBitmap( self.drawLotsGreyBitmap if start.canDrawLots else self.emptyBitmap )
		
		startPositions = start.startPositions
		Utils.AdjustGridSize( self.grid, rowsRequired = len(startPositions) )
		state = self.event.competition.state
		for row, p in enumerate(startPositions):
			rider = state.labels[p]
			self.grid.SetCellValue( row, 0, str(rider.bib) )
			self.grid.SetCellValue( row, 1, rider.full_name )
			self.grid.SetCellValue( row, 2, rider.team )
		
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )

	def commit( self ):
		pass

class EventOutcome(EnablePanel):
	def __init__(self, parent):
		EnablePanel.__init__(self, parent)
		self.box = wx.StaticBox( self, wx.ID_ANY, 'Outcome' )
		boxSizer = wx.StaticBoxSizer( self.box, wx.HORIZONTAL )
		
		self.event = None
		
		self.SetBackgroundColour( wx.WHITE )
		
		font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		self.outcomeStatus = wx.StaticText( self, wx.ID_ANY, 'Waiting for Race Outcome...' )
		self.outcomeStatus.SetFont( font )
		
		self.okButton = MakeRoundButton( self, 'OK' )
		self.restartButton = MakeRoundButton( self, 'Restart', isRestart )
		self.cancelButton = MakeRoundButton( self, 'Cancel', isCancel )
		
		boxSizer.Add( self.outcomeStatus, flag=wx.ALL|wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT, border = 8 )
		boxSizer.AddStretchSpacer()
		boxSizer.Add( self.cancelButton, flag=wx.ALL, border = 8 )
		boxSizer.AddSpacer( 32 )
		boxSizer.Add( self.restartButton, flag=wx.ALL, border = 8 )
		boxSizer.AddSpacer( 64 )
		boxSizer.Add( self.okButton, flag=wx.ALL, border = 8 )
		
		self.activeBar = wx.StaticText( self, wx.ID_ANY, '', size=(40, 0) )
		boxSizer.Add( self.activeBar, 0, flag=wx.ALL|wx.EXPAND, border = 4 )
		
		sizer = wx.BoxSizer( wx.VERTICAL )
		sizer.Add( boxSizer, 1, flag=wx.EXPAND )
		self.SetSizer( sizer )
	
	def SetEnable( self, enable ):
		EnablePanel.SetEnable( self, enable )
		for b, t in [(self.okButton, isSelect), (self.restartButton, isRestart), (self.cancelButton, isCancel)]:
			EnableRoundButton( b, enable, t )
		self.activeBar.SetBackgroundColour( wx.Colour(0, 128, 0) if enable else wx.WHITE )
		self.outcomeStatus.SetLabel( 'Waiting for Race Outcome...' if enable else '' )
		self.Refresh()

		
	def refresh( self ):
		pass
		
	def commit( self ):
		pass
	
	def setEvent( self, event ):
		self.event = event
		
class EventFinishOrderConfirmDialog( wx.Dialog ):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent)
		
		self.SetBackgroundColour( wx.WHITE )
		
		vs = wx.BoxSizer( wx.VERTICAL )
		
		font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		
		bitmap = wx.Bitmap( os.path.join(Utils.getImageFolder(), 'checkered_flag_wavy.png'), wx.BITMAP_TYPE_PNG )
		flagBitmap = wx.StaticBitmap( self, wx.ID_ANY, bitmap )
		
		title = wx.StaticText(self, wx.ID_ANY, 'Confirm Result' )
		title.SetFont( font )
		
		hsTitle = wx.BoxSizer( wx.HORIZONTAL )
		hsTitle.Add( flagBitmap, 0, flag=wx.EXPAND|wx.ALL, border = 4 )
		hsTitle.Add( title, 0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 4 )
		
		vs.Add( hsTitle, flag=wx.EXPAND )
		
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.EnableReorderRows( False )
		self.grid.CreateGrid( 2, 6 )
		self.grid.SetRowLabelSize( 0 )
		
		self.grid.SetLabelFont( font )
		
		vs.Add( self.grid, 1, flag=wx.ALL|wx.EXPAND, border = 4 )
		
		self.okButton = MakeRoundButton( self, 'OK' )
		self.cancelButton = MakeRoundButton( self, 'Cancel', isCancel )
		self.okButton.Bind( wx.EVT_BUTTON, self.onOK )
		self.cancelButton.Bind( wx.EVT_BUTTON, self.onCancel )
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		hs.Add( self.cancelButton, 0, flag=wx.ALL|wx.EXPAND, border = 4 )
		hs.AddStretchSpacer()
		hs.Add( self.okButton, 0, flag=wx.ALL|wx.EXPAND, border = 4 )
		
		vs.Add( hs, 0, flag=wx.ALL|wx.EXPAND, border = 4 )
		
		self.SetSizer( vs )
	
	def refresh( self, grid ):
		font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
	
		Utils.AdjustGridSize( self.grid, rowsRequired = grid.GetNumberRows(), colsRequired = grid.GetNumberCols() + 1 )
		self.grid.SetColLabelValue( 0, 'Pos' )
		attr = gridlib.GridCellAttr()
		attr.SetFont( font )
		attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP );
		attr.SetReadOnly( True )
		self.grid.SetColAttr( 0, attr )
		
		for col in xrange(grid.GetNumberCols()):
			headerName = grid.GetColLabelValue(col)
			self.grid.SetColLabelValue( col+1, headerName )
			attr = gridlib.GridCellAttr()
			attr.SetFont( font )
			if headerName == 'Bib':
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP );
			elif headerName.startswith('Time'):
				attr.SetRenderer( gridlib.GridCellFloatRenderer(-1, 3) )
			attr.SetReadOnly( True )
			self.grid.SetColAttr( col+1, attr )
		
		iColStatus = grid.GetNumberCols() - 2
		results = [ [grid.GetCellValue(row, col) for col in xrange(grid.GetNumberCols())] for row in xrange(grid.GetNumberRows()) ]
		results.sort( key = lambda x: x[iColStatus] )
		
		for row in xrange(grid.GetNumberRows()):
			self.grid.SetCellValue( row, 0, str(row+1) )
			for col in xrange(grid.GetNumberCols()):
				v = results[row][col]
				self.grid.SetCellValue( row, col+1, v if v != '0.000' else '' )
						
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )
		
		self.GetSizer().Layout()
		self.GetSizer().Fit( self )
		
		self.CentreOnParent(wx.BOTH)
		self.SetFocus()

	
	def onOK( self, event ):
		self.EndModal( wx.ID_OK )
		
	def onCancel( self, event ):
		self.EndModal( wx.ID_CANCEL )

	
class EventFinishOrder(EnablePanel):
	def __init__(self, parent):
		EnablePanel.__init__(self, parent)
		self.box = wx.StaticBox( self, wx.ID_ANY, 'Result' )
		boxSizer = wx.StaticBoxSizer( self.box, wx.HORIZONTAL )
		
		self.event = None
		
		self.SetBackgroundColour( wx.WHITE )
		
		self.headerNames = ['Bib', 'Name', 'Team', 'Status', 'Time    ']
		self.iColStatus = self.headerNames.index( 'Status' )
		
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.CreateGrid( 4, len(self.headerNames) )
		
		font = wx.FontFromPixelSize( wx.Size(0,FontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		self.grid.SetLabelFont( font )
		for col in xrange(self.grid.GetNumberCols()):
			self.grid.SetColLabelValue( col, self.headerNames[col] )
			self.grid.SetCellValue( 0, col, self.headerNames[col] )		# Add the label as data.
			attr = gridlib.GridCellAttr()
			attr.SetFont( font )
			if self.headerNames[col] == 'Bib':
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP );
				attr.SetReadOnly( True )
			elif self.headerNames[col].startswith('Time'):
				attr.SetEditor( gridlib.GridCellFloatEditor(-1, 3) )
				attr.SetRenderer( gridlib.GridCellFloatRenderer(-1, 3) )
			elif col == 1 or col == 2:
				attr.SetReadOnly( True )
			elif col == self.iColStatus:
				attr.SetEditor( gridlib.GridCellChoiceEditor(choices = ['Rel', 'DQ', 'DNF', '']) )
			self.grid.SetColAttr( col, attr )
		
		self.grid.AutoSizeColumns( False )								# Resize to fit the column name.
		self.grid.AutoSizeRows( False )
		for col in xrange(self.grid.GetNumberCols()):
			self.grid.SetCellValue( 0, col, '' )						# Remove the labels.
		
		boxSizer.Add( self.grid, 1, flag=wx.ALL|wx.EXPAND, border = 4 )
		
		vs = wx.BoxSizer( wx.VERTICAL )	
		self.okButton = MakeRoundButton( self, 'OK' )
		self.cancelButton = MakeRoundButton( self, 'Cancel', isCancel )
		vs.Add( self.okButton, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM, border = 4 )
		vs.Add( self.cancelButton, flag=wx.ALL, border = 4 )
		
		boxSizer.Add( vs, 0, flag=wx.ALL, border = 4 )
		
		self.activeBar = wx.StaticText( self, wx.ID_ANY, '', size=(40, 0) )
		boxSizer.Add( self.activeBar, 0, flag=wx.ALL|wx.EXPAND, border = 4 )
		
		sizer = wx.BoxSizer( wx.VERTICAL )
		sizer.Add( boxSizer, 1, flag=wx.EXPAND )
		self.SetSizer( sizer )
	
	def SetEnable( self, enable ):
		EnablePanel.SetEnable( self, enable )
		for b, t in [(self.okButton, isSelect), (self.cancelButton, isCancel)]:
			EnableRoundButton( b, enable, t )
		self.activeBar.SetBackgroundColour( wx.Colour(0, 128, 0) if enable else wx.WHITE )
		self.Refresh()
		
	def setEvent( self, event ):
		self.event = event
	
	def refresh( self ):
		if not self.event:
			self.grid.ClearGrid()
			return
		
		# Guess finish order by qualifying time.
		state = self.event.competition.state
		finishPositions = sorted( self.event.starts[-1].startPositions, key = lambda r: state.labels[r].qualifyingTime )
		Utils.AdjustGridSize( self.grid, rowsRequired = len(finishPositions) )
		
		state = self.event.competition.state
		for row, p in enumerate(finishPositions):
			rider = state.labels[p]
			self.grid.SetCellValue( row, 0, str(rider.bib) )
			self.grid.SetCellValue( row, 1, rider.full_name )
			self.grid.SetCellValue( row, 2, rider.team )
			self.grid.SetCellValue( row, 3, '' )
			self.grid.SetCellValue( row, 4, '' )
		
		self.grid.AutoSizeColumns( False )
		self.grid.AutoSizeRows( False )

	def commit( self ):
		if not self.event:
			self.grid.ClearGrid()
			return

		places = []
		times = []
		for row in xrange(self.grid.GetNumberRows()):
			bib = self.grid.GetCellValue( row, 0 )
			try:
				bib = int(bib)
			except:
				continue
			status = self.grid.GetCellValue( row, self.iColStatus )
			places.append( (bib, status) )
			
			try:
				t = float( self.grid.GetCellValue( row, self.grid.GetNumberCols() - 1) )
			except ValueError:
				continue
			times.append( (row+1, t) )
		
		start = self.event.starts[-1]
		start.setPlaces( places )
		start.setTimes( times )
		
		self.event.propagate()
		Model.model.setChanged( True )
		Model.model.competition.propagate()
		Utils.setTitle()
		
class Events(wx.Panel):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self, parent):
		"""Constructor"""
		wx.Panel.__init__(self, parent)
		
		self.eventSelect = EventSelect( self )
		self.eventPosition = EventPosition( self )
		self.eventOutcome = EventOutcome( self )
		self.eventResult = EventFinishOrder( self )
		
		sizer = wx.BoxSizer( wx.VERTICAL )
		sizer.Add( self.eventSelect, 1, flag=wx.EXPAND|wx.ALL, border = 4 )
		sizer.Add( self.eventPosition, 0, flag=wx.EXPAND|wx.ALL, border = 4 )
		sizer.Add( self.eventOutcome, 0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border = 4 )
		sizer.Add( self.eventResult, 0, flag=wx.EXPAND|wx.ALL, border = 4 )
		
		self.setState( 0 )
		
		self.eventSelect.selectButton.Bind( wx.EVT_BUTTON, self.doEventSelectSelect )
		
		self.eventPosition.startButton.Bind( wx.EVT_BUTTON, self.doEventPositionStart )
		self.eventPosition.cancelButton.Bind( wx.EVT_BUTTON, self.doEventPositionCancel )
		
		self.eventOutcome.okButton.Bind( wx.EVT_BUTTON, self.doEventOutcomeOK )
		self.eventOutcome.restartButton.Bind( wx.EVT_BUTTON, self.doEventOutcomeRestart )
		self.eventOutcome.cancelButton.Bind( wx.EVT_BUTTON, self.doEventOutcomeCancel )
		
		self.eventResult.okButton.Bind( wx.EVT_BUTTON, self.doEventResultOK )
		self.eventResult.cancelButton.Bind( wx.EVT_BUTTON, self.doEventResultCancel )
		
		self.resultConfirmDialog = EventFinishOrderConfirmDialog( self )
		self.restartDialog = RestartDialog( self )
		
		self.SetSizer(sizer)
	
	def getGrid( self ):
		return self.eventSelect.grid
		
	#-------------------------------------------------------------------------
	def doEventSelectSelect( self, e ):
		if not self.eventSelect.grid.GetNumberRows():
			return
		selectedRows = self.eventSelect.grid.GetSelectedRows()
		if not selectedRows:
			return
		event = self.eventSelect.events[selectedRows[0]]
		event.getStart()
		self.eventSelect.event = event
		self.eventPosition.event = event
		self.eventResult.event = None
		self.event = event
		Model.model.setChanged( True )
		Utils.setTitle()
		self.setState( 1 )
		
	#-------------------------------------------------------------------------
	def doEventPositionStart( self, e ):
		self.setState( 2 )
		
	def doEventPositionCancel( self, e ):
		del( self.event.starts[-1] )
		Model.model.setChanged( True )
		Utils.setTitle()
		self.reset()
		
	#-------------------------------------------------------------------------
	def doEventOutcomeOK( self, e ):
		self.eventResult.event = self.event
		self.setState( 3 )
		
	def doEventOutcomeRestart( self, e ):
		self.restartDialog.refresh( self.event )
		if self.restartDialog.ShowModal() == wx.ID_OK:
			self.event.getStart()
			Model.model.setChanged( True )
			Utils.setTitle()
			self.setState( 1 )
		
	def doEventOutcomeCancel( self, e ):
		self.setState( 1 )
	
	#-------------------------------------------------------------------------
	def doEventResultOK( self, e ):
		self.resultConfirmDialog.refresh( self.eventResult.grid )
		if self.resultConfirmDialog.ShowModal() == wx.ID_OK:
			self.eventResult.commit()
			Model.model.setChanged( True )
			Utils.setTitle()
			self.reset()
		
	def doEventResultCancel( self, e ):
		self.eventResult.event = None
		self.setState( 2 )
	
	#-------------------------------------------------------------------------
	def setState( self, newState ):
		for i, p in enumerate([self.eventSelect, self.eventPosition, self.eventOutcome, self.eventResult]):
			p.SetEnable( i == newState )
			if p != self.eventSelect and i != newState:
				try:
					p.grid.ClearSelection()
				except AttributeError:
					pass
		self.state = newState
		self.refresh()
	
	def refresh( self ):
		for p in [self.eventSelect, self.eventPosition, self.eventOutcome, self.eventResult]:
			p.refresh()
		
	def commit( self ):
		pass
		
	def reset( self ):
		self.eventSelect.event = None
		self.eventPosition.event = None
		self.eventResult.event = None
		self.setState( 0 )
		
########################################################################

class EventsFrame(wx.Frame):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		wx.Frame.__init__(self, None, title="Events Test", size=(1000,800) )
		self.panel = Events(self)
		self.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
	app = wx.App(False)
	SetDefaultData()
	frame = EventsFrame()
	app.MainLoop()