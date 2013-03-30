import wx
import Model
from Competitions import SetDefaultData
from Utils import WriteCell
from Events import FontSize
import cPickle as pickle

class GraphDraw( wx.Panel ):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, wx.ID_ANY)
		
		self.selectedRider = None
		self.SetDoubleBuffered( True )
		
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_MOTION, self.OnMotion)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		
		self.rectRiders = []
		self.colX = []

	def OnMotion( self, evt):
		x, y = evt.GetX(), evt.GetY()
		for i in xrange(len(self.colX)):
			if self.colX[i] <= x < self.colX[i+1]:
				for rect, riders in self.rectRiders[i]:
					if rect.ContainsXY(x, y):
						if self.selectedRider != rider:
							self.selectedRider = rider;
							wx.CallAfter( self.refresh )
							break
	
	def OnSize(self, evt):
		wx.CallAfter( self.Refresh )
	
	def OnPaint(self, evt):
		dc = wx.BufferedPaintDC(self)
		self.Draw(dc)

	def refresh( self ):
		self.Refresh()
		
	def Draw(self, dc):
		gc = wx.GraphicsContext.Create( dc )
		
		width, height = self.GetClientSize()
		
		gc.SetBrush( wx.WHITE_BRUSH )
		gc.DrawRectangle( 0, 0, width, height )
		gc.SetBrush( wx.BLACK_BRUSH )
			
		model = Model.model
		competition = model.competition
		state = competition.state
		
		def riderName( id ):
			try:
				return state.labels[id].full_name
			except:
				return ''
	
		grid = [[{'title':'Qualifiers'}, {}]]
		for i in xrange(1, competition.starters+1):
			grid[0].extend( [{'name':riderName('N%d'%i),'out':'N%d' % i}, {}] )
			
		for tournamentCount, tournament in enumerate(competition.tournaments):
			if tournamentCount == 0:
				rowStart = 0
				col = 1
			else:
				rowStart = len(grid[1])
				col = 2
				
			while len(grid) <= col:
				grid.append( [] )
			
			if tournament.name:
				grid[col].extend( [{}] * (rowStart - len(grid[col])) )
				grid[col].extend( [{'title': 'Tournament "%s"' % tournament.name}, {}] )
				rowStart += 2
			for s, system in enumerate(tournament.systems):
				while len(grid) <= col:
					grid.append( [] )
					
				grid[col].extend( [{}] * (rowStart - len(grid[col])) )
				grid[col].extend( [{'title':system.name}, {}] )
				for event in system.events:
					if 'Repechages' in system.name and event.i == 0:
						grid[col].extend( [{}] * (len(grid[col-1]) - len(grid[col])) )
					elif len(event.composition) == 4:	# Offset the 4-ways to another column.
						rowLast = len(grid[col])
						if 'Repechages' in system.name:
							rowLast -= (4+1)
						col += 1
						while len(grid) <= col:
							grid.append( [] )
						grid[col].extend( [{}] * (rowLast - len(grid[col])) )
						
					out = [event.winner] + event.others
					riderOut = dict( (state.labels[o], o) for o in out if state.labels.get(o, state.OpenRider) != state.OpenRider )
					for c in event.composition:
						values = {'in':c}
						try:
							values['out'] = riderOut[state.labels[c]]
						except KeyError:
							pass
						if len(event.composition) != 4 and 'out' in values:
							values['winner'] = (values['out'] == event.winner)
							
						grid[col].append( values )
					grid[col].append( {} )
				col += 1
	
		results, dnfs, dqs = model.competition.getResults()
		grid.append( [{'title':'Results'}, {}] )
		for i, rider in enumerate(results):
			grid[-1].append( {'in':'R%d' % (i+1),'name':rider.full_name if rider else '', 'rider':rider} )
			grid[-1].append( {} )
	
		outCR = {}
		inCR = {}
		for c, col in enumerate(grid):
			for r, v in enumerate(col):
				if 'out' in v:
					outCR[v['out']] = (c, r)
				if 'in' in v:
					inCR[v['in']] = (c, r)
	
		fontSize = 0.4 * height / model.competition.starters
		fontSizeMin, fontSizeMax = 0.0, fontSize * 3
		while 1:
			fontSize = int((fontSizeMax + fontSizeMin) / 2.0)
			
			font = gc.CreateFont( wx.FontFromPixelSize(wx.Size(0,fontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL) )
			boldFont = gc.CreateFont( wx.FontFromPixelSize(wx.Size(0,fontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD) )
			gc.SetFont( font )
			textWidth, textHeight, textDescent, textExternalLeading = gc.GetFullTextExtent( 'My What a Nice String!' )
			rowHeight = textHeight * 1.15
			
			colWidths = [0] * len(grid)
			for c, col in enumerate(grid):
				for v in col:
					if 'title' in v:
						gc.SetFont( boldFont )
						colWidths[c] = max( colWidths[c], gc.GetFullTextExtent(v['title'])[0] )
						gc.SetFont( font )
					elif 'name' in v:
						colWidths[c] = max( colWidths[c], gc.GetFullTextExtent(v['name'])[0] )
					if 'in' in v and state.labels.get( v['in'], None):
						colWidths[c] = max( colWidths[c], gc.GetFullTextExtent(riderName(v['in']))[0] )
			
			border = 8
			xLeft = border
			yTop = border
			colX = [xLeft]
			colSpace = rowHeight * 5
			for c, w in enumerate(colWidths):
				colX.append( colX[-1] + w + colSpace )

			rows = max( len(col) for col in grid )
			if colX[len(grid)] - colSpace > width - border or rows * rowHeight > height:
				fontSizeMax = fontSize
			else:
				if fontSizeMax - fontSizeMin < 1.001:
					break
				fontSizeMin = fontSize
		
		whiteFont = gc.CreateFont( wx.FontFromPixelSize(wx.Size(0,fontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL), wx.WHITE )
		greenPen = gc.CreatePen( wx.Pen(wx.Colour(0,200,0)) )
		greenPenThick = gc.CreatePen( wx.Pen(wx.Colour(0,200,0), 4) )
		redPen = gc.CreatePen( wx.RED_PEN )
		redPenThick = gc.CreatePen( wx.Pen(wx.Colour(255,0,0), 4) )
		blackPen = gc.CreatePen( wx.BLACK_PEN )
		bluePen = gc.CreatePen( wx.Pen(wx.Colour(0,0,200)) )
		whitePen = gc.CreatePen( wx.WHITE_PEN )
		blackBrush = gc.CreateBrush( wx.BLACK_BRUSH )
		whiteBrush = gc.CreateBrush( wx.WHITE_BRUSH )
		gc.SetBrush( blackBrush )
		
		gc.SetBrush( whiteBrush )
		#gc.DrawRectangle( 0, 0, width, height )
		
		def addSCurve( path, x1, y1, x2, y2 ):
			controlRatio = 0.50
			cx1, cy1 = x2 - (x2 - x1)*controlRatio, y1
			cx2, cy2 = x1 + (x2 - x1)*controlRatio, y2
			path.AddCurveToPoint( cx1, cy1, cx2, cy2, x2, y2 )
		
		# Draw the connections.
		for c, col in enumerate(grid):
			for r, v in enumerate(col):
				if 'out' not in v or not riderName(v['out']):
					continue
				rider = state.labels[v['out']]
				x1 = colX[c] + gc.GetFullTextExtent(riderName(v['out']))[0]
				y1 = yTop + r * rowHeight + rowHeight / 2
				
				try:
					cTo, rTo = inCR[v['out']]
				except KeyError:
					continue
				
				x2 = colX[cTo]
				y2 = yTop + rTo * rowHeight + rowHeight / 2
				
				if 'winner' in v:
					if rider == self.selectedRider:
						gc.SetPen( greenPenThick if v['winner'] else redPenThick )
					else:
						gc.SetPen( greenPen if v['winner'] else redPen )
				else:
					gc.SetPen( greenPenThick if rider == self.selectedRider else greenPen )
				
				path = gc.CreatePath()
				path.MoveToPoint( x1, y1 )
				addSCurve( path, x1, y1, x2, y2 )
				gc.StrokePath( path )
			
		# Create a map of the last event for all riders.
		riderLastEvent = {}
		for cFrom in xrange(len(grid)-2, -1, -1):
			for rFrom, vFrom in enumerate(grid[cFrom]):
				try:
					rider = state.labels[vFrom['out']]
				except KeyError:
					continue
				if rider not in riderLastEvent:
					riderLastEvent[rider] = (cFrom, rFrom)
						
		def getIsBlocked( cFrom, rFrom, cTo, rTo ):
			for c in xrange(cFrom+1, cTo):
				for r in xrange( min(rFrom, rTo), min(max(rFrom, rTo), len(grid[c])) ):
					if 'in' in grid[c][r]:
						return True
			return False
			
		# Draw the connections to the results.
		colAvoidCount = [6 if competition.starters == 24 else 1] * len(grid)
		cTo = len(grid) - 1
		for rTo, v in enumerate(grid[-1]):
			try:
				id = v['in']
			except KeyError:
				continue
			rider = results[int(id[1:]) - 1]
			if rider not in riderLastEvent:
				continue
				
			cFrom, rFrom = riderLastEvent[rider]
			
			gc.SetPen( greenPenThick if rider == self.selectedRider else greenPen )
				
			x1 = colX[cFrom] + gc.GetFullTextExtent(rider.full_name)[0]
			y1 = yTop + rFrom * rowHeight + rowHeight / 2
			x2 = colX[cTo]
			y2 = yTop + rTo * rowHeight + rowHeight / 2
			path = gc.CreatePath()
			path.MoveToPoint( x1, y1 )
			
			if competition.starters == 18 or not getIsBlocked(cFrom, rFrom, cTo, rTo):
				addSCurve( path, x1, y1, x2, y2 )
			else:
				maxRowBetween = max( len(grid[c]) for c in xrange(cFrom+1, cTo) )
				xa = colX[cFrom+1]
				rAvoid = maxRowBetween + colAvoidCount[cFrom]
				colAvoidCount[cFrom] += 2
				ya = yTop + rAvoid * rowHeight
				addSCurve( path, x1, y1, xa, ya )
				for cNext in xrange(cFrom+2, cTo+1):
					if not getIsBlocked(cNext, rAvoid, cTo, rTo):
						break
				xb = colX[min(cNext+1, len(grid)-1)] - colSpace
				yb = ya
				path.AddLineToPoint( xb, yb )
				addSCurve( path, xb, yb, x2, y2 )
				
			gc.StrokePath( path )
		
		def drawName( name, x, y, selected ):
			if not name:
				return
			if selected:
				gc.SetFont( whiteFont )
				xborder = fontSize / 2
				yborder = fontSize / 10
				width, height = gc.GetFullTextExtent(name)[:2]
				gc.SetBrush( blackBrush )
				gc.SetPen( blackPen )
				gc.DrawRoundedRectangle( x-xborder, y-yborder, width + xborder*2, height + yborder*2, (height + yborder*2) / 4 )
				gc.DrawText( name, x, y, blackBrush )
				gc.SetFont( font )
			else:
				gc.DrawText( name, x, y )
		
		riderNames = dict( (state.labels[n].full_name, state.labels[n])
			for n in ['N%d' % i for i in xrange(1, competition.starters+1)] if n in state.labels )
		
		# Draw the node names.
		self.rectRiders = []
		for c, col in enumerate(grid):
			colRects = []
			for r, v in enumerate(col):
				x = colX[c]
				y = yTop + r * rowHeight
				if 'title' in v:
					gc.SetFont( boldFont )
					gc.DrawText( v['title'], x, y )
					gc.SetFont( font )
				elif 'name' in v:
					rider = v.get('rider', None) or riderNames.get(v['name'], None)
					if rider:
						colRects.append( (wx.Rect(x, y, gc.GetFullTextExtent(rider.full_name)[0], rowHeight), rider) )
						drawName( rider.full_name, x, y, rider == self.selectedRider )
				elif 'in' in v and riderName(v['in']):
					rider = state.labels.get(v['in'], None)
					if rider:
						drawName( rider.full_name, x, y, rider == self.selectedRider )
						colRectsappend( (wx.Rect(x, y, gc.GetFullTextExtent(rider.full_name)[0], rowHeight), rider) )
				elif 'out' in v and riderName(v['out']):
					rider = state.labels.get(v['out'], None)
					if rider:
						colRectsappend( (wx.Rect(x, y, gc.GetFullTextExtent(rider.full_name)[0], rowHeight), rider) )
			self.rectRiders.append( colRects )
		self.rectRiders.append( (colX[len(grid), []) )
		self.colX = colX
					
		
########################################################################

class GraphDrawFrame(wx.Frame):
	""""""
 
	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		wx.Frame.__init__(self, None, title="Graph Test", size=(1000,800) )
		panel = GraphDraw(self)
		panel.refresh()
		self.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
	app = wx.App(False)
	#SetDefaultData()
	with open(r'Races\TestFinished.smr', 'rb') as fp:
		Model.model = pickle.load( fp )
	frame = GraphDrawFrame()
	app.MainLoop()