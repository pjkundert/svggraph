#!/usr/bin/env python
"""\
SVGgraph.py - Construct/display SVG scenes, with support for simple graphs.

The following code is a lightweight wrapper around SVG files. The metaphor
is to construct a scene, add objects to it, and then write it to a file
to display it.

This program uses ImageMagick to display the SVG files. ImageMagick also 
does a remarkable job of converting SVG files into other formats.
"""

__author__ = "Perry Kundert (perry@kundert.ca)"
__copyright__ = "Copyright 2006, Perry Kundert"
__contributors__ = []
__version__ = "1.0.1 $Rev:$"
__license__ = "GPL"
__history__ = """

"""

import os
import sys
import cgi
import cgitb
import ImageColor	

cgitb.enable()

display_prog = 'display' # Command to execute to display images.
      
class Scene:
    def __init__(self,name="svg",height=400,width=400):
        self.name = name
        self.items = []
        self.height = height
        self.width = width
        return

    def add(self,item): self.items.append(item)

    def strarray(self):
        var = ["<?xml version=\"1.0\"?>\n",
               "<svg xmlns=\"http://www.w3.org/2000/svg\" height=\"%d\" width=\"%d\" >\n" % (self.height,self.width),
               " <g style=\"fill-opacity:1.0; stroke:black;\n",
               "  stroke-width:1;\">\n"]
        for item in self.items: var += item.strarray()            
        var += [" </g>\n</svg>\n"]
        return var

#    def write_svg(self,filename=None):
#        if filename:
#            self.svgname = filename
#        else:
#            self.svgname = self.name + ".svg"
#        file = open(self.svgname,'w')
#        file.writelines(self.strarray())
#        file.close()
#        return
#
#    def display(self,prog=display_prog):
#        os.system("%s %s" % (prog,self.svgname))
#        return        


class Line:
    def __init__(self,start,end):
        self.start = start #xy tuple
        self.end = end     #xy tuple
        return

    def strarray(self):
        return ["  <line x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\" />\n" %\
                (self.start[0],self.start[1],self.end[0],self.end[1])]


class Circle:
    def __init__(self,center,radius,color,stroke=None):
        self.center = center #xy tuple
        self.radius = radius #xy tuple
        self.color = color   #rgb tuple in range(0,256) or None
	self.stroke = stroke #rbg tuple in range(0,256) or None
        return

    def strarray(self):
	try:    strkcol = colorstr( self.stroke )
	except: strkcol = "none"
	try:    fillcol = colorstr( self.color )
	except: fillcol = "none"

        return [ "  <circle cx=\"%d\" cy=\"%d\" r=\"%d\"\n" %\
		 ( self.center[0], self.center[1], self.radius ),
                "    style=\"stroke: %s; fill: %s;\" />\n" %\
		 ( strkcol, fillcol ) ]

class Rectangle:
    def __init__(self,origin,height,width,color,stroke=None):
        self.origin = origin
        self.height = height
        self.width = width
        self.color = color
        self.stroke = stroke
        return

    def strarray(self):
	try:    strkcol = colorstr( self.stroke )
	except: strkcol = "none"
	try:    fillcol = colorstr( self.color )
	except: fillcol = "none"
        return ["  <rect x=\"%d\" y=\"%d\" height=\"%d\"\n" %\
                (self.origin[0],self.origin[1],self.height),
                "    width=\"%d\" style=\"stroke: %s; fill: %s;\" />\n" %\
                ( self.width, strkcol, fillcol ) ]

class Text:
    def __init__( self, origin, text, stroke=None, size="24pt" ):
        self.origin = origin
        self.text = text
	self.stroke = stroke
        self.size = size
        return

    def strarray(self):
	try:    strkcol = colorstr( self.stroke )
	except: strkcol = "#000000"
        return ["  <text x=\"%d\" y=\"%d\" font-size=\"%s\" style=\"stroke: %s\">\n" %\
                ( self.origin[0], self.origin[1], self.size, strkcol ),
                "   %s\n" % self.text,
                "  </text>\n"]

class Comment:
    def __init__( self, text ):
	self.text = text

    def strarray( self ):
        return [ "<!-- %s -->\n" % self.text ]
        
    
def colorstr( rgb ):
    return "#%02x%02x%02x" % ( rgb[0], rgb[1], rgb[2] )

# 
# Graph
# 
#    Add points.  Will auto-scale both axes to the given graph size.
# 
class Graph:
    def __init__( self, origin, height, width, style = "smooth", line = 1 ):
	self.origin = origin		# upper left corner of graph (in screen coordinates)
	self.height = height		# total size of graph
	self.width = width
	self.style = style
	self.line = line

        self.xmin = (0,0)
        self.xmax = (0,0)
        self.ymin = (0,0)
        self.ymax = (0,0)
	self.extents = False

	self.points = {}		# dictionary keyed on label, of lists of coordinate 2-tuples
	self.colors = {}		# dictionary keyed on label, colors in hex form #RRGGBB
	return

    # Add data point(s), and (latest) axes min/max.  Can handle either a list of 2-tuples, or a
    # single 2-tuple.  
    def data( self, things, label = '', color = ( 0, 0, 0 )):
	if not self.points.has_key( label ):
	    self.points[label] = []
	    self.colors[label] = color
	
	list = []
	if type( things ) != type( [] ):
	    list = [ things ]
	else:
	    list = things
	for point in list:
	    if self.extents:
		if point[0] <= self.xmin[0]:
		    self.xmin = point
		if point[0] >= self.xmax[0]:
		    self.xmax = point
		if point[1] <= self.ymin[1]:
		    self.ymin = point
		if point[1] >= self.ymax[1]:
		    self.ymax = point
	    else:
		self.extents = True
		self.xmin = point
		self.xmax = point
		self.ymin = point
		self.ymax = point
	    self.points[label].append( point )

    # Returns the calculated axis scales for the graph.  These are used to transform the data points
    # into screen coordinates relative to the graph's zero point.  Account for the line weight.
    def scale( self ):
	return ( float( self.width  - self.line ) / ( 1, self.xmax[0] - self.xmin[0] )[self.xmax[0] != self.xmin[0]],
		 float( self.height - self.line ) / ( 1, self.ymax[1] - self.ymin[1] )[self.ymax[1] != self.ymin[1]] )

    # Returns the calculated zero point (in screen coordinates), relative to the origin.  After each
    # data point is scaled, add this value to transform it into screen coordinates relative to the
    # origin.  Screen y axis is inverted, remember, compared to graph y axis.  The 1/2 of the line weight
    # would extend beyond each edge of the display; the scale above accounts for both the upper/lower
    # and top/bottom edge's line weigth.
    def zero( self, scl ):
        return ( -int( self.xmin[0] * scl[0] ) + self.line/2,
                 -int( self.ymin[1] * scl[1] ) + self.line/2)

    # Compute the graph coordinates of a point, relative to (0,0) in the LL corner
    def graph( self, pnt, scl, zro ):
        return ( pnt[0] * scl[0] + zro[0],
		 pnt[1] * scl[1] + zro[1] )

    # Compute the screen coordinates of a graph point
    def screen( self, gra ):
        return ( self.origin[0] + 0           + gra[0],
		 self.origin[1] + self.height - gra[1] )

    # Transform a given datum into the scale of the graph, and offset by the graph's zero point.
    # Remember, the SVG scene's origin is the upper left, the graph's origin is the lower left...
    def transform( self, pnt, scl = None, zro = None ):
	if not scl: scl = self.scale()
	if not zro: zro = self.zero( scl )
	return self.screen( self.graph( pnt, scl, zro ))

    # Returns the transformed graph data points in the specified SVG form (line graph, by default)
    def strarray( self ):
	res = []
	scl = self.scale()
	zro = self.zero( scl )
	segs = self.ymax[1] - self.ymin[1] + 1 				# segment count and size, used for "discrete" only
	seg = self.height / segs

        for label in self.points.keys():                		# key is label
            if len( self.points[label] ) > 1:
                if self.style != "random":                  		# implies "smooth", too
                  self.points[label].sort()                 		# nothing else necessary!  tuples sort ok! ( cmp = lambda a, b: a[0] - b[0] )
                lst = self.transform( self.points[label][0], scl, zro )
                if  self.style != "discrete":
                    # smooth, step or random
                    axi = "  <polyline points=\"%d %d" % lst
                    for raw in self.points[label][1:]:
                        pnt = self.transform( raw, scl, zro )
                        if self.style == "step":
                            axi += ", %d %d" % ( pnt[0], lst[1] )
                        axi += ", %d %d" % pnt
                        lst = pnt
                    axi += "\" style=\"stroke: %s; stroke-width: %d; fill: none;\" />\n" % ( colorstr( self.colors[label] ), self.line )
                    res.append( axi )
                else:
                    # discrete
		    res.append( " <g style=\"stroke-width: %d\">\n" % ( self.line ))
                    for raw in self.points[label]:
                        gra = self.graph( raw, scl, zro )
			pct = gra[1] * 100 / self.height
			bot = ( gra[0], gra[1] - self.line - seg * pct / 100  )
			top = ( gra[0], bot[1] + self.line + seg )
			bot = self.screen( bot )
			top = self.screen( top )
                        res.append( "  <line x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\" style=\"stroke: %s\"/>\n" \
				    % ( bot[0], bot[1], top[0], top[1], colorstr( self.colors[label] )))
		    res.append( " </g>\n" )
	return res

def test():
    scene = Scene('test')
    scene.add(Rectangle((100,100),200,200,(0,255,255)))
    scene.add(Line((200,200),(200,300)))
    scene.add(Line((200,200),(300,200)))
    scene.add(Line((200,200),(100,200)))
    scene.add(Line((200,200),(200,100)))
    scene.add(Circle((200,200),30,(0,0,255)))
    scene.add(Circle((200,300),30,(0,255,0)))
    scene.add(Circle((300,200),30,(255,0,0)))
    scene.add(Circle((100,200),30,(255,255,0)))
    scene.add(Circle((200,100),30,(255,0,255)))
    scene.add(Text((50,50),"Testing SVG"))

    graph = Graph( (100,100), 100, 300 )
    graph.data( (100,100) )
    graph.data( (150,150) )
    graph.data( (200,100) )
    graph.data( (250,300) )
    scene.add( graph )

    scene.write_svg( "/tmp/test.svg" )
    scene.display()
    return

# Return the named query's value, or the default.  If it is a list (query was supplied multiple
# times), return the last one.
def param( form, name, default ):
    if form.has_key( name ):
        if type( form[name] ) == type( [] ):
	    return form[name][-1].value
	else:
	    return form[name].value
    else:
	return default

def content( type = "text/html" ):
    print "Content-type: " + type
    print "Status: 200 Ok"
    print "ETag: " + str(hash(os.environ['QUERY_STRING'] + __version__))
    print ""

def error( status = "Status: 400 Bad Request", errors = [] ):
    print "Content-type: text/plain"
    print status 
    print ""
    print status 
    print ""
    print "Specify one or more graph data sets, with optional color name:"
    print " Label=#,#..."
    print " Label=color:#,#..."
    print " Label=color:# #,# #,..."
    print ""
    print "Options:"
    print "  height=#      Graph height in pixels.  Padded if max/min requested"
    print "   width=#      Graph width in pixels.   Padded if legend requested"
    print "     max=color  Maxima dot, with value printed in same color (unless legend=none,... specified)"
    print "     min=color  Minima dot, with value printed in same color (unless legend=none,... specified)"
    print " decimal=#      Min/Maxima values are scaled by this power of 10 when printed"
    print "  legend=...    none, bottom/top, min, max, all:  Display selected legends."
    print "   style=...    smooth (the default), step, discrete, random: Graph style."
    print "   format=...   svg (the default), png, jpg, gif, (only svg works in the Google App Engine version)..."
    print ""
    print "Examples:"
    print ""
    print "    A simple sine wave, with implicit linear X axis:"
    print ""
    print "        http://svggraph.appspot.com?sin=0,30,58,80,95,100,95,80,58,30,0,-30,-58,-80,-95,-100,-95,-80,-58,-30,0"
    print ""
    print "    A sine wave with a logarithmic X axis:"
    print ""
    print "        http://svggraph.appspot.com?sin=0 0, 100 30,158 58,200 80,232 95,258 100,280 95,300 80,316 58,332 30,345 0,358 -30,370 -58,380 -80,390 -95,400 -100,408 -95,416 -80,424 -58,432 -30,439 0,445 30,452 58,458 80,464 95,470 100,475 95,480 80,485 58,490 30,495 0,500 -30,504 -58,508 -80,512 -95,516 -100,520 -95,524 -80,528 -58,532 -30,535 0"
    print ""
    if errors:
        sys.stdout.writelines( errors )
    sys.stdout.writelines( [ k + ": " + str( os.environ[k] ) + "\n" for k in os.environ.keys() ] )
    #sys.exit()

# If called directly, see if we are being invoked as CGI or not.
if __name__ == '__main__':
    try:
        if not os.environ['REQUEST_METHOD'] in ['GET', 'HEAD']:
	    error( "Status: 405 Method Not Allowed: %s" % os.environ['REQUEST_METHOD'] )
    except:
	# Not CGI (no 'REQUEST_METHOD' found).  Do a test...
	test()
	sys.exit()
    
    # It's CGI and an allowed request.  Try to process, and return an error on exception
    form = cgi.FieldStorage()

    # Extract the known CGI query options (or assume defaults)
    querys = [ 'style', 'height', 'width', 'line', 'min', 'max', 'decimal', 'legend', 'format' ]
    styl = param( form, 'style',	'smooth' )
    high = param( form, 'height',	'18' )
    wide = param( form, 'width',	'100' )
    line = param( form, 'line',		'1' )				# line weight
    minc = param( form, 'min', 		'' )
    maxc = param( form, 'max',		'' )
    deci = param( form, 'decimal',	'0' )				# shift decimal place by this +/- factor of 10
    lgnd = param( form, 'legend',	'' )				# No legend by default
    fmat = param( form, 'format',       'svg' )

    if styl not in [ 'smooth', 'step', 'discrete', 'random' ]:
	error( "Status: 400 Bad Request: Unrecognized style option: %s" % styl )
    try:
	deci = int( deci )
    except:
	error( "Status: 400 Bad Request: Unrecognized decimal offset option: %s" % deci )
	
    lgndmn = minc and 1 or 0
    lgndmx = maxc and 1 or 0
    lgndlb = None
    for l in lgnd.split(','):
        if l == "none":
	    lgndmn = 0; lgndmx = 0; lgndlb = None
	elif l == "all":
	    lgndmn = 1; lgndmx = 1; lgndlb = "bottom"
	elif l == "bottom" or l == "top":
	    lgndlb = l
	elif l == "min":
	    lgndmn = 1
	elif l == "max":
	    lgndmx = 1
	elif l != '':
	    error( "Status: 400 Bad Request: Unrecognized legend option: %s" % l )

    # Determines if extra padding required due to line size and max./minima dots.
    lsiz = max( 1, int( line ))						# Requested line size, minimum 1
    lpad = 0
    if minc or maxc:
        lpad = max( 2, lsiz )						# Max./minima dots are 2 pixels radius, or line width (if selected)
    graph = Graph( ( lpad, lpad ),
		   int( high ), int( wide ),
		   styl, lsiz )

    # Get the data set(s).  They may be tuples or values (deduce x axis).  All the remaining
    # query options are assumed to be the named (and optionally the colored) data sets, if they
    # look like:
    # 
    #     name=[color:]#,#,...
    # or: name=[color:]# #,# #,...
    comment = ""
    for key in [ k for k in form.keys() if k not in querys ]:
        data = param( form, key,	'' )

	# Try to pick a color:#,#,... off the front of the data; default to "black".  Convert color
	# to an RBG 3-tuple (#,#,#)
        label = key
        color = "black"
        try: color,data = data.split(':')
        except: pass
	strkcol = ImageColor.getrgb( color )

        # If we fail while trying to parse the coordinates, or if we CAN parse it, and there are no
        # values, it's an error.
        list = []
 	try:
            for item in data.split(','):
                if item:
                    coord = item.split()
                    if len( coord ) == 2:
                        # A full coordinate pair!  Use it.  Mixing 1 and 2+ coords not suggested, after any have been deduced...
                        list.append( ( int( coord[0] ), int( coord[1] )))
                    elif len( coord ) == 1:
                        # Not a coordinate pair.  Deduce X from last 0, 1 or 2+ coords.
                        if len( list ) == 0:
                            list.append( ( 0, int( coord[0] )))
                        elif len( list ) == 1:
                            list.append( ( list[-1][0] + 1, int( coord[0] )))
                        else:
                            list.append( ( list[-1][0] + ( list[-1][0] - list[-2][0] ), int( coord[0] )))
        except:
	    error( "Status: 400 Bad Request: Unrecognized query: %s=%s" % ( key, param( form, key, '' )))
        if not len( list ):
	    error( "Status: 400 Bad Request: Label %s had no data" % label )
	comment += "\nLabel: %s\n  color: %s\n  data: %s\n  coords: %s\n"\
	    		% ( label, color, data, ', '.join( [ "%d %d" % ( x, y ) for x,y in list ] ))
	graph.data( list, label, strkcol )

    if not graph.colors.keys():
	error( "Status: 400 Bad Request: No graph data set(s) supplied" )

    # Create the scene.  Legend across bottom (if multiple axes), maxima/minima stacked on right.
    # Font size in pixels, is minimum of 1/5 100dpi (5 pitch on 100dpi) or 1/2 the height, and 1/6
    # inter-line spacing.
    flin = min( 100 / 5, ( int( high ) + 2 * lpad ) / 2 )		# Font line
    fsiz = flin * 5 / 6							# Font size
    fpad = flin - fsiz							# Hence, the font inter-line pad
    fwgt = fsiz * 1 / 6							# and approx weight of font

    # Determine total padding around graph, based on max./minima legend and/or label legend display
    mnum = 0								# Number of max./minima chars
    if lgndmn: mnum = max( mnum, len( str( graph.ymin[1] * 10 ** deci )))
    if lgndmx: mnum = max( mnum, len( str( graph.ymax[1] * 10 ** deci )))
    hpad = 0
    if mnum:
        hpad += int( line ) + fsiz / 2 + mnum * fsiz * 2 / 3		# glyphs ~ 2/3 wide as high? 1/2 glyph spacing at start
    vpad = 0
    if lgndlb:
	vpad += flin

    # Graph is padded on all sides by 'lpad', if any max./minima selected
    scene = Scene( 'graph',
		   int( high ) + 2 * lpad + vpad,
		   int( wide ) + 2 * lpad + hpad )
    # scene.add( Comment( comment ))
    scene.add( graph )

    # Draw graph min/max points if desired (one maxima/minima for ALL axes!)
    if minc:
	scene.add( Circle( graph.transform( graph.ymin ), lpad,
			   ImageColor.getrgb( minc )))
    if lgndmn:
	scene.add( Text(  (int( wide ) + int( line ) + fsiz / 2, int( high ) -    0 ), str( graph.ymin[1] * 10 ** deci ),
			  ImageColor.getrgb( minc and minc or "black" ), str( fsiz ) + "px" ))
    if maxc:
	scene.add( Circle( graph.transform( graph.ymax ), lpad,
			   ImageColor.getrgb( maxc )))
    if lgndmx:
	scene.add( Text(  (int( wide ) + int( line ) + fsiz / 2, int( high ) - flin ), str( graph.ymax[1] * 10 ** deci ),
			  ImageColor.getrgb( maxc and maxc or "black" ), str( fsiz ) + "px" ))

    if lgndlb:  # TODO: allow legend at "top"
	x = 0
	for label in graph.colors.keys():
            # glyphs will descend below scene by 1/2 of their stroke weight
	    scene.add( Text(  ( x * int( wide )/len( graph.colors.keys()), int( high ) + flin - fwgt / 2), label,
			      graph.colors[label], str( fsiz ) + "px" ))
	    x += 1

    # All OK.  Output the (native) SVG content, or 'convert' to some other format!
    if fmat == "svg":
        content( "image/svg+xml" )
	sys.stdout.writelines( scene.strarray())
    else:
#        # Some other graphics format.  Convert to it.  Assume they
#        # know what they are talking about.
#        to,fr,er = os.popen3( "convert svg:- " + fmat + ":-" )
#        to.writelines( scene.strarray() )
#        to.close()
#        pid,exi = os.wait()
#        if exi:
#            # Didn't work; non-zero exit code.  Probably a bad image format.
#            errors = er.readlines() + fr.readlines()
            errors = ""
            error( "Status: 400 Bad Request: Error converting to format 'image/" + fmat, errors )
#
#        content( "image/" + fmat )
#        sys.stdout.write( fr.read() )
#        fr.close()
#        er.close()
        
