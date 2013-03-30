
import wx
import os
import xlwt
import Utils
import Model
import math
import cgi
import base64
from FitSheetWrapper import FitSheetWrapper
from contextlib import contextmanager

#---------------------------------------------------------------------------

@contextmanager
def tag( buf, name, attrs = {} ):
	if isinstance(attrs, str) and attrs:
		attrs = { 'class': attrs }
	buf.write( '<%s>' % ' '.join(
			[name] + ['%s="%s"' % (attr, value) for attr, value in attrs.iteritems()]
		) )
	yield
	buf.write( '</%s>\n' % name )

brandText = 'Powered by SprintMgr (sites.google.com/site/crossmgrsoftware)'

def ImageToPil( image ):
	"""Convert wx.Image to PIL Image."""
	w, h = image.GetSize()
	data = image.GetData()

	redImage = Image.new("L", (w, h))
	redImage.fromstring(data[0::3])
	greenImage = Image.new("L", (w, h))
	greenImage.fromstring(data[1::3])
	blueImage = Image.new("L", (w, h))
	blueImage.fromstring(data[2::3])

	if image.HasAlpha():
		alphaImage = Image.new("L", (w, h))
		alphaImage.fromstring(image.GetAlphaData())
		pil = Image.merge('RGBA', (redImage, greenImage, blueImage, alphaImage))
	else:
		pil = Image.merge('RGB', (redImage, greenImage, blueImage))
	return pil

class ExportGrid( object ):
	PDFLineFactor = 1.10

	def __init__( self, title, grid ):
		self.title = title
		self.grid = grid
		self.colnames = [grid.GetColLabelValue(c) for c in xrange(grid.GetNumberCols())]
		self.data = [ [grid.GetCellValue(r, c) for r in xrange(grid.GetNumberRows())] for c in xrange(grid.GetNumberCols()) ]
		
		self.fontName = 'Helvetica'
		self.fontSize = 16
		
		self.leftJustifyCols = {}
		self.rightJustifyCols = {}
		
		rightJustify = set( ['Pos', 'Bib', 'Time'] )
		for c, n in enumerate(self.colnames):
			if n in rightJustify:
				self.rightJustifyCols[c] = True
			else:
				self.leftJustifyCols[c] = True
	
	def getHeaderGraphic( self ):
		return os.path.join(Utils.getImageFolder(), 'SprintMgr.png')
		
	def getHeaderBitmap( self ):
		bitmap = wx.Bitmap( self.getHeaderGraphic(), wx.BITMAP_TYPE_PNG )
		return bitmap

	def _getFont( self, pixelSize = 28, bold = False ):
		return wx.FontFromPixelSize( (0,pixelSize), wx.FONTFAMILY_SWISS, wx.NORMAL,
									 wx.FONTWEIGHT_BOLD if bold else wx.FONTWEIGHT_NORMAL, False, 'Ariel' )
	
	def _getColSizeTuple( self, dc, font, col ):
		wSpace, hSpace, lh = dc.GetMultiLineTextExtent( '    ', font )
		extents = [ dc.GetMultiLineTextExtent(self.colnames[col], font) ]
		extents.extend( dc.GetMultiLineTextExtent(str(v), font) for v in self.data[col] )
		return max( e[0] for e in extents ), sum( e[1] for e in extents ) + hSpace/4
	
	def _getDataSizeTuple( self, dc, font ):
		wSpace, hSpace, lh = dc.GetMultiLineTextExtent( '    ', font )
		
		wMax, hMax = 0, 0
		
		# Sum the width of each column.
		for col, c in enumerate(self.colnames):
			w, h = self._getColSizeTuple( dc, font, col )
			wMax += w + wSpace
			hMax = max( hMax, h )
			
		if wMax > 0:
			wMax -= wSpace
		
		return wMax, hMax
	
	def _drawMultiLineText( self, dc, text, x, y ):
		if not text:
			return
		wText, hText, lineHeightText = dc.GetMultiLineTextExtent( text, dc.GetFont() )
		for line in text.split( '\n' ):
			dc.DrawText( line, x, y )
			y += lineHeightText

	def _getFontToFit( self, widthToFit, heightToFit, sizeFunc, isBold = False ):
		left = 1
		right = max(widthToFit, heightToFit)
		
		while right - left > 1:
			mid = (left + right) / 2.0
			font = self._getFont( mid, isBold )
			widthText, heightText = sizeFunc( font )
			if widthText <= widthToFit and heightText <= heightToFit:
				left = mid
			else:
				right = mid - 1
		
		return self._getFont( left, isBold )
	
	def drawToFitDC( self, dc ):
		# Get the dimentions of what we are printing on.
		(widthPix, heightPix) = dc.GetSizeTuple()
		
		# Get a reasonable border.
		borderPix = max(widthPix, heightPix) / 20
		
		widthFieldPix = widthPix - borderPix * 2
		heightFieldPix = heightPix - borderPix * 2
		
		xPix = borderPix
		yPix = borderPix
		
		graphicWidth = 0
		graphicHeight = heightPix * 0.15
		graphicBorder = 0
		qrWidth = 0
		
		# Draw the graphic.
		bitmap = self.getHeaderBitmap()
		bmWidth, bmHeight = bitmap.GetWidth(), bitmap.GetHeight()
		graphicHeight = heightPix * 0.12
		graphicWidth = float(bmWidth) / float(bmHeight) * graphicHeight
		graphicBorder = int(graphicWidth * 0.15)

		# Rescale the graphic to the correct size.
		# We cannot use a GraphicContext because it does not support a PrintDC.
		image = bitmap.ConvertToImage()
		image.Rescale( graphicWidth, graphicHeight, wx.IMAGE_QUALITY_HIGH )
		if dc.GetDepth() == 8:
			image = image.ConvertToGreyscale()
		bitmap = image.ConvertToBitmap( dc.GetDepth() )
		dc.DrawBitmap( bitmap, xPix, yPix )
		image, bitmap = None, None
		
		# Draw the title.
		font = self._getFontToFit( widthFieldPix - graphicWidth - graphicBorder - qrWidth, graphicHeight,
									lambda font: dc.GetMultiLineTextExtent(self.title, font)[:-1], True )
		dc.SetFont( font )
		self._drawMultiLineText( dc, self.title, xPix + graphicWidth + graphicBorder, yPix )
		yPix += graphicHeight + graphicBorder
		
		heightFieldPix = heightPix - yPix - borderPix
		
		# Draw the table.
		font = self._getFontToFit( widthFieldPix, heightFieldPix, lambda font: self._getDataSizeTuple(dc, font) )
		dc.SetFont( font )
		wSpace, hSpace, textHeight = dc.GetMultiLineTextExtent( '    ', font )
		
		# Get the max height per row.
		rowHeight = [0] * (self.grid.GetNumberRows() + 1)
		for r in xrange(self.grid.GetNumberRows()):
			rowHeight[r] = max( dc.GetMultiLineTextExtent(self.grid.GetCellValue(r, c), font)[1] for c in xrange(self.grid.GetNumberCols()))
		
		yPixTop = yPix
		yPixMax = yPix
		for col, c in enumerate(self.colnames):
			colWidth = self._getColSizeTuple( dc, font, col )[0]
			yPix = yPixTop
			w, h, lh = dc.GetMultiLineTextExtent( c, font )
			if col in self.leftJustifyCols:
				self._drawMultiLineText( dc, str(c), xPix, yPix )					# left justify
			else:
				self._drawMultiLineText( dc, str(c), xPix + colWidth - w, yPix )	# right justify
			yPix += h + hSpace/4
			if col == 0:
				yLine = yPix - hSpace/8
				dc.DrawLine( borderPix, yLine, widthPix - borderPix, yLine )
				for r in rowHeight:
					yLine += r
					dc.DrawLine( borderPix, yLine, widthPix - borderPix, yLine )
					
			for r, v in enumerate(self.data[col]):
				vStr = str(v)
				if vStr:
					w, h, lh = dc.GetMultiLineTextExtent( vStr, font )
					if col in self.leftJustifyCols:
						self._drawMultiLineText( dc, vStr, xPix, yPix )					# left justify
					else:
						self._drawMultiLineText( dc, vStr, xPix + colWidth - w, yPix )	# right justify
				yPix += rowHeight[r]
			yPixMax = max(yPixMax, yPix)
			xPix += colWidth + wSpace
				
		# Put CrossMgr branding at the bottom of the page.
		font = self._getFont( borderPix // 5, False )
		dc.SetFont( font )
		w, h, lh = dc.GetMultiLineTextExtent( brandText, font )
		self._drawMultiLineText( dc, brandText, borderPix, heightPix - borderPix + h )
	
	def toExcelSheet( self, sheet ):
		''' Write the contents of the grid to an xlwt excel sheet. '''
		titleStyle = xlwt.XFStyle()
		titleStyle.font.bold = True
		titleStyle.font.height += titleStyle.font.height / 2
		
		rowTop = 0
		if self.title:
			for line in self.title.split('\n'):
				sheet.write(rowTop, 0, line, titleStyle)
				rowTop += 1
			rowTop += 1
		
		sheetFit = FitSheetWrapper( sheet )
		
		# Write the colnames and data.
		rowMax = 0
		for col, c in enumerate(self.colnames):
			headerStyle = xlwt.XFStyle()
			headerStyle.borders.bottom = xlwt.Borders.MEDIUM
			headerStyle.font.bold = True
			headerStyle.alignment.horz = xlwt.Alignment.HORZ_LEFT if col in self.leftJustifyCols \
																	else xlwt.Alignment.HORZ_RIGHT
			headerStyle.alignment.wrap = xlwt.Alignment.WRAP_AT_RIGHT
			
			style = xlwt.XFStyle()
			style.alignment.horz = xlwt.Alignment.HORZ_LEFT if col in self.leftJustifyCols \
																	else xlwt.Alignment.HORZ_RIGHT
			style.alignment.wrap = True
			style.alignment.vert = xlwt.Alignment.VERT_TOP
			
			sheetFit.write( rowTop, col, c, headerStyle, bold=True )
			for row, v in enumerate(self.data[col]):
				rowCur = rowTop + 1 + row
				if rowCur > rowMax:
					rowMax = rowCur
				sheetFit.write( rowCur, col, v, style )
				
		# Add branding at the bottom of the sheet.
		style = xlwt.XFStyle()
		style.alignment.horz = xlwt.Alignment.HORZ_LEFT
		sheet.write( rowMax + 2, 0, brandText, style )
		
	def toHtml( self, buf ):
		''' Write the contents to the buffer in HTML format. '''
		
		with tag(buf, 'table', {'class': 'TitleTable'} ):
			with tag(buf, 'tr'):
				with tag(buf, 'td', dict(valign='top')):
					data = base64.b64encode(open(self.getHeaderGraphic(),'rb').read())
					buf.write( '<img id="idImgHeader" src="data:image/png;base64,%s" />' % data )
				with tag(buf, 'td'):
					buf.write( '&nbsp;&nbsp;&nbsp;&nbsp;' )
				with tag(buf, 'td'):
					with tag(buf, 'span', {'id': 'idRaceName'}):
						buf.write( cgi.escape(self.title).replace('\n', '<br/>\n') )
					if Model.model.organizer:
						with tag(buf, 'br'):
							pass
						with tag(buf, 'span', {'id': 'idOrganizer'}):
							buf.write( 'by ' )
							buf.write( cgi.escape(Model.model.organizer) )
		
		with tag(buf, 'table', {'class': 'results'} ):
			with tag(buf, 'thead'):
				with tag(buf, 'tr'):
					for col in self.colnames:
						with tag(buf, 'th'):
							buf.write( cgi.escape(col).replace('\n', '<br/>\n') )
			with tag(buf, 'tbody'):
				for row in xrange(max(len(d) for d in self.data)):
					with tag(buf, 'tr'):
						for col in xrange(self.grid.GetNumberCols()):
							with tag(buf, 'td', {'class':'rAlign'} if col not in self.leftJustifyCols else {}):
								try:
									buf.write( cgi.escape(self.data[col][row]).replace('\n', '<br/>\n') )
								except IndexError:
									buf.write( '&nbsp;' )
									
		with tag(buf, 'p', {'class': 'smallfont'}):
			buf.write( 'Powered by ' )
			with tag(buf, 'a', dict(href="http://www.sites.google.com/site/crossmgrsoftware")):
				buf.write( 'SprintMgr' )
		return buf
			
if __name__ == '__main__':
	pass
