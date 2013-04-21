# This derived class adds to the functionality of the PyRSS2Gen Classes...

# Copyright [2007]. California Institute of Technology.  ALL RIGHTS RESERVED.
# U.S. Government sponsorship acknowledged. Any commercial use must be
# negotiated with the Office of Technology Transfer at the California
# Institute of Technology.

# This software is subject to U. S. export control laws and regulations
# (22 C.F.R. 120-130 and 15 C.F.R. 730-774). To the extent that the
# software is subject to U.S. export control laws and regulations, the
# recipient has the responsibility to obtain export licenses or other
# export authority as may be required before exporting such information
# to foreign countries or providing access to foreign nationals.

import datetime
import PyRSS2Gen
import pickle

import os
import os.path
import ConfigParser

# Get tools for line simplification and great circle geometry
import PolyTools
import GeoTools

_generator_name = "Datacasting Feed Publishing Tools"

# It turns out that UTC is not an RFC-822 compliant time zone. :)
# So, just ignore the following...
# Override the PyRSS2Gen Date formatter to say 'UTC' not 'GMT'
def Datacasting_format_date(dt):
    """convert a datetime into an RFC 822 formatted date

    Input date must be in GMT.
    """
    # Looks like:
    #   Sat, 07 Sep 2002 00:00:01 GMT
    # Can't use strftime because that's locale dependent
    #
    # Isn't there a standard way to do this for Python?  The
    # rfc822 and email.Utils modules assume a timestamp.  The
    # following is based on the rfc822 module.
    return "%s, %02d %s %04d %02d:%02d:%02d UTC" % (
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()],    
            dt.day,
            ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][dt.month-1],
            dt.year, dt.hour, dt.minute, dt.second)

# It turns out that UTC is not an RFC-822 compliant time zone. :)
# PyRSS2Gen._format_date = Datacasting_format_date

##############################################
# Support Element Classes with Publish Methods
##############################################
class FloatElement:
  """implements the 'publish' API for floats
  
  Takes the tag name and the integer value to publish.
  """
  element_attrs = {}
  def __init__(self, name, val):
    self.name = name
    self.val = float(val)
  def publish(self, handler):
    handler.startElement(self.name, self.element_attrs)
    handler.characters(str(self.val))
    handler.endElement(self.name)


##################################
# CHANNEL LEVEL Element Extensions
##################################
class Format:
  def __init__(self):
    pass
  def publish(self, handler):
    pass

class CustomEltDef:
  element_attrs = {}
  def __init__(self, name = None, type = None, min = None, max = None,
               displayName = None, units = None, configTuple = None):
    self.name        = None
    self.type        = None
    self.displayName = None
    self.units       = None
    self.min         = None
    self.max         = None

    if (configTuple is None):
      self.name = name
      self.type = type
      self.displayName = displayName
      self.units = units
      self.min = min
      self.max = max
    else:
      if (len(configTuple) >= 2):
        self.name        = configTuple[0]
        self.type        = configTuple[1]
      if (len(configTuple) >= 3):
        self.displayName  = configTuple[2]
      if (len(configTuple) >= 4):
        self.units = configTuple[3]
      
      
  def publish(self, handler):
    self.element_attrs = { 'name' : self.name, 'type' : self.type }
    if self.displayName is not None:
      self.element_attrs['displayName'] = self.displayName
    if self.units is not None:
      self.element_attrs['units'] = self.units
    if self.min is not None:
      self.element_attrs['min'] = self.min
    if self.max is not None:
      self.element_attrs['max'] = self.max
    PyRSS2Gen._element(handler,
                       "datacasting:customEltDef", None,
                       self.element_attrs)


###############################
# ITEM LEVEL Element Extensions
###############################
class CustomElement:
  element_attrs = {}
  def __init__(self, name, value):
    self.name = name
    self.value = value
  def publish(self, handler):
    self.element_attrs = { 'name' : self.name }
    if isinstance(self.value, str):
      self.element_attrs['value'] = self.value
      PyRSS2Gen._element(handler,
                         "datacasting:customElement", None,
                         self.element_attrs)
    else:
      handler.startElement("datacasting:customElement", self.element_attrs)
      self.value.publish(handler)
      handler.endElement("datacasting:customElement")
      
      

class ExtentsPoly:  
  """Publish the extents of the data granule"""
  whereElement_attrs = {} 
  polygonElement_attrs = {}
  exteriorElement_attrs = {}
  linearRingElement_attrs = {}
  posListElement_attrs = {}
  
  def __init__(self, listLatLonPairs, simplifyPolygon = True,
               polyDistThresh = 5.0, polyMaxPoints = 256):
    if ((len(listLatLonPairs) > 3) and
        (listLatLonPairs[0] == listLatLonPairs[-1])):
      if simplifyPolygon:
        newPairs = PolyTools.ramerDouglasStough(listLatLonPairs,
                     polyDistThresh, polyMaxPoints, GeoTools.gcDistXtrack)
        self.listLatLonPairs = newPairs
      else:
        self.listLatLonPairs = listLatLonPairs
    else:
      print "ERROR: A polygon is 4 or more lat lon pairs where the first"
      print "       and last pair are identical."
      print ""
      print "listLatLonPairs: %s" % listLatLonPairs
      raise
  
  def publish(self, handler):
    handler.startElement("georss:where", self.whereElement_attrs)
    handler.startElement("gml:Polygon", self.polygonElement_attrs)
    handler.startElement("gml:exterior", self.exteriorElement_attrs)
    handler.startElement("gml:LinearRing", self.linearRingElement_attrs)
    PyRSS2Gen._element(handler,
                       "gml:posList",
                       (' '.join([ ('%f %f' % (x,y))
                                   for (x,y) in self.listLatLonPairs])),
                       self.posListElement_attrs)
    handler.endElement("gml:LinearRing")
    handler.endElement("gml:exterior")
    handler.endElement("gml:Polygon")
    handler.endElement("georss:where")


class Extents:  
  """Publish the extents of the data granule"""
  whereElement_attrs = {}
  envelopeElement_attrs = {}
  lcElement_attrs = {}
  ucElement_attrs = {}
  def __init__(self,
               lcLat,  # lower corner latitude
               lcLon,  # lower corner longitude
               ucLat,  # upper corner latitude
               ucLon,  # upper corner longitude
               ):
    self.lcLat = lcLat
    self.lcLon = lcLon
    self.ucLat = ucLat
    self.ucLon = ucLon

  def asPoly(self):
    points = [ (self.ucLat, self.ucLon),
               (self.ucLat, self.lcLon),
               (self.lcLat, self.lcLon),
               (self.lcLat, self.ucLon),
               (self.ucLat, self.ucLon)  ]
    return ExtentsPoly(points)

  def publish(self, handler):
    handler.startElement("georss:where", self.whereElement_attrs)
    handler.startElement("gml:Envelope", self.envelopeElement_attrs)
    PyRSS2Gen._element(handler,
                       "gml:lowerCorner",
                       ("%f %f" % (self.lcLat, self.lcLon)),
                       self.lcElement_attrs)
    PyRSS2Gen._element(handler,
                       "gml:upperCorner",
                       ("%f %f" % (self.ucLat, self.ucLon)),
                       self.ucElement_attrs)
    handler.endElement("gml:Envelope")
    handler.endElement("georss:where")


class cePoint:
  """Represent and publish the Custom Element type 'Point'"""
  whereElement_attrs = {}
  pointElement_attrs = {}
  posElement_attrs = {}
  def __init__(self, lat, lon):
    self.lat = lat
    self.lon = lon
  def publish(self, handler):
    handler.startElement("georss:where", self.whereElement_attrs)
    handler.startElement("gml:Point", self.pointElement_attrs)
    PyRSS2Gen._element(handler,
                       "gml:pos",
                       ("%f %f" % (self.lat, self.lon)),
                       self.posElement_attrs)
    handler.endElement("gml:Point")
    handler.endElement("georss:where")
    

  

#######################
# Feed and Item Classes
#######################
class Feed(object, PyRSS2Gen.RSS2):

  rss_attrs = {"version": "2.0",
               # The Datacasting Namespace
               "xmlns:datacasting" :
               "http://datacasting.jpl.nasa.gov/datacasting",
               # GEORSS required by Datacasting for the georss:where element
               "xmlns:georss" :
               "http://www.georss.org/georss",
               # GML required by GEORSS for specifying location
               "xmlns:gml" :
               "http://www.opengis.net/gml"}
  
  def __init__(self,

               # Standard RSS Elements
               title = None,
               link = None,
               description = None,

               language = None,
               copyright = None,
               managingEditor = None,
               webMaster = None,
               pubDate = None,  # a datetime, *in* *GMT*
               lastBuildDate = None, # a datetime

               categories = None, # list of strings or Category
               generator = _generator_name,
               docs = "http://datacasting.jpl.nasa.gov/datacasting.html",
               cloud = None,    # a Cloud
               ttl = None,      # integer number of minutes

               image = None,     # an Image
               rating = None,    # a string; I don't know how it's used
               textInput = None, # a TextInput
               skipHours = None, # a SkipHours with a list of integers
               skipDays = None,  # a SkipDays with a list of strings

               items = None,     # list of RSSItems

               # Datacasting Specific Elements
               dataSource = None,    # a string indicating the data source
               # a string which is unique to the channel and is used by
               # the client to form the directory tree in which
               # downloaded data is stored
               channelUID = "default",
               customEltDefList = None, # a list of CustomEltDef(s)
               format = None, # a Format describing the data
               ):
    PyRSS2Gen.RSS2.__init__(self, title, link, description, language,
                            copyright, managingEditor, webMaster,
                            pubDate , lastBuildDate, categories,
                            generator, docs, cloud, ttl, image,
                            rating, textInput, skipHours, skipDays,
                            items)

    self.dataSource       = dataSource
    self.channelUID       = channelUID
    self.customEltDefList = customEltDefList
    self.format           = format

    # Set up a lookup on custom element name
    self.customEltDefNameHash = {}

    if customEltDefList is not None:
      for ced in customEltDefList:
        self.customEltDefNameHash[ced.name] = ced


  def FromConfig(klass, cp):
    if not cp.has_section('Feed'):
      print "ERROR: no Feed section present in config file"
      return None

    if cp.has_option('Feed','skiphours'):
      skipHours      = eval("PyRSS2Gen.SkipHours([ %s ])" %
                            cp.get('Feed','skiphours'))
    else:
      skipHours = None

    if cp.has_option('Feed','skipdays'):
      skipDays       = eval("PyRSS2Gen.SkipDays([ %s ])" %
                            cp.get('Feed','skipdays'))
    else:
      skipDays = None

    if cp.has_section('Feed/Image'):
      image = PyRSS2Gen.Image(
        url            = eval(cp.get('Feed/Image','url')),
        title          = eval(cp.get('Feed/Image','title',
                                     dne = 'None')),
        description    = eval(cp.get('Feed/Image','description',
                                     dne = 'None')),
        link           = eval(cp.get('Feed/Image','link',
                                     dne = 'None')),
        width          = eval(cp.get('Feed/Image','width',
                                     dne = 'None')),
        height         = eval(cp.get('Feed/Image','height',
                                     dne = 'None')),)
    else:
      image = None

    customEltDefList = []
    if cp.has_section('Feed/CustomElements'):
      for ceItem in cp.items('Feed/CustomElements'):
        tup = eval(ceItem[1])
        ce  = CustomEltDef(configTuple = tup)
        customEltDefList.append(ce)
    else:
      customEltDefList = None

    # TODO: Integrate ESML formatting here
    format = None
    
    rss = klass(title          = eval(cp.get('Feed','title')),
                link           = eval(cp.get('Feed','link')),
                description    = eval(cp.get('Feed','description')),
                channelUID     = eval(cp.get('Feed','channeluid',
                                             dne = '"default"')), 
                dataSource     = eval(cp.get('Feed','datasource',
                                             dne = 'None')),
                language       = eval(cp.get('Feed','language',
                                             dne = 'None')),
                copyright      = eval(cp.get('Feed','copyright',
                                             dne = 'None')),
                managingEditor = eval(cp.get('Feed','managingeditor',
                                             dne = 'None')),
                webMaster      = eval(cp.get('Feed','webmaster',
                                             dne = 'None')),
                rating         = eval(cp.get('Feed','rating',
                                             dne = 'None')),
                ttl            = eval(cp.get('Feed','ttl',
                                             dne = 'None')),
                skipHours      = skipHours,
                skipDays       = skipDays,
                image          = image,
                format         = format,
      
                customEltDefList = customEltDefList,)
    return rss
  FromConfig = classmethod(FromConfig)
  


  def write_xml(self, outfile, encoding = "UTF-8"):
    PyRSS2Gen.WriteXmlMixin.write_xml(self, outfile, encoding)


      
  def publish_extensions(self, handler):
    """Datacasting extensions to the RSS2 Publish functionality"""
    PyRSS2Gen._opt_element(handler, "datacasting:channelUID",
                           self.channelUID)
    PyRSS2Gen._opt_element(handler, "datacasting:dataSource",
                           self.dataSource)
    if type(self.customEltDefList) is list:
      for eltDef in self.customEltDefList:
        eltDef.publish(handler)
        
    if self.format is not None:
      self.format.publish(handler)



  def SaveXML(self, filename):
    self.write_xml(open(filename,'w'))

    



class Item(object, PyRSS2Gen.RSSItem):
  """Publish a Datacasting Item"""
  def __init__(self,
               
               # Standard PyRSS2Gen Elements
               title = None,  # string
               link = None,   # url as string
               description = None, # string
               author = None,      # email address as string
               categories = None,  # list of string or Category
               comments = None,  # url as string
               enclosure = None, # an Enclosure
               guid = None,    # a unique string
               pubDate = None, # a datetime
               source = None,  # a Source

               # Datacasting specific elements
               acquisitionStartDate = None, # a datetime in GMT
               acquisitionEndDate = None,   # a datetime in GMT
               acquisitionDuration = None,  # a floating point number in seconds
               extents = None,              # an Extents
               enclosureList = None,        # a list of Enclosure(s)
               customElementList = None,    # a list of CustomElement(s)
               preview = None,              # a URL pointing to a thumbnail
               productName = None,          # the filename used to save the
                                            # product

               # Pregenerated Item XML
               xmlFileName = None,  # The filename of an item.write_xml() file

               # Read Item from text file,
               txtFileName = None,
               # Parent feed: needed when processing item from text file
               parentFeed = None,

               # Additional Configuration info in a dict
               addlConfig = {},
               ):
    # RSS Item Inits
    self.title       = None
    self.link        = None
    self.description = None
    self.author      = None
    self.categories  = []
    self.comments    = None
    self.enclosure   = None
    self.guid        = None
    self.pubDate     = None
    self.source      = None

    # Datacasting Item Specific Inits
    preInit                   = False
    self.xmlOnly              = False
    self.acquisitionStartDate = None
    self.acquisitionEndDate   = None
    self.acquisitionDuration  = None
    self.extents              = None
    self.enclosureList        = None
    self.customElementList    = None
    self.preview              = None
    self.productName          = None

    # Interpret Additional Config
    if 'simplifyPolygons' in addlConfig:
      self.simplifyPolygons = addlConfig['simplifyPolygons']
    else:
      self.simplifyPolygons = False
    if 'polyMaxPoints' in addlConfig:
      self.polyMaxPoints = addlConfig['polyMaxPoints']
    else:
      self.polyMaxPoints = None
    if 'polyDistThresh' in addlConfig:
      self.polyDistThresh = addlConfig['polyDistThresh']
    else:
      self.polyDistThresh = None
    
    # Loading Item as XML snippet -- This block of text will be inserted
    # into the output RSS feed channel element without checking or
    # verification.
    #
    # WARNING:  Garbage in, garbage out.
    if xmlFileName is not None:
      self.xmlOnly = True
      self.xmlLines = file(xmlFileName, 'r').readlines()
      preInit = True
      return

    # Read in values for the constructor from a TSV text file with one
    # line per attribute.  Per line: first value = variable name;
    # additional values = used to build variables.
    #
    # WARNING: Format and syntax is critical and error messages won't help.
    if txtFileName is not None:
      self.parentFeed = parentFeed
      self.ReadFromTextFile(txtFileName)
      preInit = True

    if not preInit:
      PyRSS2Gen.RSSItem.__init__(self, title, link, description, author,
                                 categories, comments, enclosure, guid,
                                 pubDate, source)
    else:
      if title is not None:        self.title       = title
      if link is not None:         self.link        = link
      if description is not None:  self.description = description
      if author is not None:       self.author      = author
      if categories is not None:   self.categories  = categories
      if comments is not None:     self.comments    = comments
      if enclosure is not None:    self.enclosure   = enclosure
      if guid is not None:         self.guid        = guid
      if pubDate is not None:      self.pubDate     = pubDate
      if source is not None:       self.source      = source

    if acquisitionStartDate is not None:
      self.acquisitionStartDate = acquisitionStartDate
    if acquisitionEndDate is not None:
      self.acquisitionEndDate = acquisitionEndDate
    if acquisitionDuration is not None:
      self.acquisitionDuration = acquisitionDuration
    if extents is not None: self.extents = extents
    if enclosureList is not None: self.enclosureList = enclosureList
    if customElementList is not None: self.customElementList = customElementList
    if preview is not None: self.preview = preview                           
    if productName is not None: self.productName = productName


  # Item Constructor which loads the item from a pickled file
  def FromPickleFile(klass, filename):
    inItem = pickle.load(file(filename, 'r'))
    return inItem
  FromPickleFile = classmethod(FromPickleFile)



  # Set up Item attributes based on a simple text file format
  def ReadFromTextFile(self, txtFileName):

    if not os.path.lexists(txtFileName):
      print "WARNING: Item text file does not exist.  Empty Item created."
      return

    fileLines = file(txtFileName, 'r').readlines()
    # Process each line in the data file
    lineNum = 0
    for line in fileLines:
      lineNum = lineNum + 1
      try: 
        lineList = [ x.strip() for x in line.split("=",1) ]

        # Skip comment and blank lines
        if (lineList[0].startswith("#") or (lineList[0] == "")):
          continue

        # Detect badly formed item lines
        if (lineList[1] == ''):
          raise Exception, "no valid 'name = value' pair"

        # GIUD element
        if lineList[0] == 'guid':
          self.guid = PyRSS2Gen.Guid(lineList[1])

        # ENCLOSURE element
        elif lineList[0] == 'enclosure':
          if self.enclosureList is None:
            self.enclosureList = []
          s = [ x.strip() for x in lineList[1].split(",") ]
          self.enclosureList.append(
            PyRSS2Gen.Enclosure(s[0], int(s[1]), s[2]))

        # CUSTOMELEMENT element
        # These elements may vary based on the 'type' defined in the config
        # file, so this may be a bit tricky...
        elif lineList[0] == 'customElement':
          # Create self.customElementList if necessary.  Should be since we're
          # reading from a file...
          if self.customElementList is None:
            self.customElementList = []
          # Tease out element name
          (name, value) = [ x.strip() for x in lineList[1].split(",",1) ]
          # If we know the parent feed, we understand the types of the
          # custom elements...
          if self.parentFeed is not None:
            type = self.parentFeed.customEltDefNameHash[name].type
            # If the type is a complex type, we need to build a value object
            # and pass it along so that custom XML publish methods can be called
            if (type == 'point'):
              (lat, lon) = [ x.strip() for x in value.split(",") ]
              value = cePoint(float(lat), float(lon))
            elif (type == 'envelope'):
              ### FIXME - future support for georss envelope custom element 
              pass

            # Single value types are just passed along to be included as
            # strings in the XML

          self.customElementList.append(CustomElement(name, value))

        # Extents element
        elif lineList[0] == 'extents':
          s = lineList[1].split(",")
          self.extents = Extents(float(s[0]), float(s[1]),
                                 float(s[2]), float(s[3]))
          
        # ExtentsPoly element
        elif lineList[0] == 'extentsPoly':
          s = lineList[1].split(",")
          if (len(s)/2 == len(s)/2.0):
            listLatLon = [ (float(s[i]), float(s[i+1]))
                           for i in range(0, len(s), 2) ]
            if self.simplifyPologons:
              self.extents = ExtentsPoly(listLatLon,
                                         self.simplifyPolygons,
                                         self.polyDistThresh,
                                         self.polyMaxPoints)
            else:
              self.extents = ExtentsPoly(listLatLon, simplifyPolygons = False)

        # All datetime object elements
        elif ((lineList[0] == 'acquisitionStartDate') or
              (lineList[0] == 'acquisitionEndDate') or
              (lineList[0] == 'acquisitionStartTime') or
              (lineList[0] == 'acquisitionEndTime') or
              (lineList[0] == 'pubDate')):
          s = [ int(x.strip()) for x in lineList[1].split(":") ]
          dtEvalStr = ("datetime.datetime(" +
                       ", ".join([str(x) for x in s]) +
                       ")")
          # We are standardizing on Date, not Time special case patch (YUCK)
          if ((lineList[0] == 'acquisitionStartTime') or
              (lineList[0] == 'acquisitionEndTime')) :
            lineList[0] = lineList[0].replace('Time','Date')

          # Write it into the Dictionary...
          self.__dict__[lineList[0]] = eval(dtEvalStr)

        # All other simple single string elements
        else:
          self.__dict__[lineList[0]] = lineList[1]
          
      except Exception, inst:
        print "WARNING: Badly formed Item text file line..."
        print "  Exception: %s" % inst
        print "  %d:  %s" % (lineNum, line.strip())
        print "  Line skipped."


  def write_xml(self, outfile, encoding = "UTF-8"):
    PyRSS2Gen.WriteXmlMixin.write_xml(self, outfile, encoding)


      
  def publish(self, handler):
    if not self.xmlOnly: 
      PyRSS2Gen.RSSItem.publish(self, handler)
    else:
      handler._out.writelines(self.xmlLines[1:])



  def publish_extensions(self, handler):
    """Datacasting extensions to the RSSItem Publish functionality"""
    aST = self.acquisitionStartDate
    if isinstance(aST, datetime.datetime):
      aST = PyRSS2Gen.DateElement("datacasting:acquisitionStartDate",
                                  aST)
    PyRSS2Gen._opt_element(handler, "datacasting:acquisitionStartDate", aST)

    aET = self.acquisitionEndDate
    if isinstance(aET, datetime.datetime):
      aET = PyRSS2Gen.DateElement("datacasting:acquisitionEndDate",
                                  aET)
    PyRSS2Gen._opt_element(handler, "datacasting:acquisitionEndDate", aET)

    aD = self.acquisitionDuration
    if aD is not None:
      aD = FloatElement("datacasting:acquisitionDuration", aD)
    PyRSS2Gen._opt_element(handler, "datacasting:acquisitionDuration", aD)

    if self.extents is not None:
      self.extents.publish(handler)
      
    if type(self.enclosureList) is list:
      for enc in self.enclosureList:
        enc.publish(handler)

    if type(self.customElementList) is list:
      for cutomElt in self.customElementList:
        cutomElt.publish(handler)

    PyRSS2Gen._opt_element(handler, "datacasting:preview", self.preview)
    PyRSS2Gen._opt_element(handler, "datacasting:productName", self.productName)



  # Save item as PICKLED text  
  def Save(self, filename):
    pickle.dump(self, file(filename, 'w'))



  # Save item as XML snippet.  It will not be 
  def SaveXML(self, filename):
    self.write_xml(open(filename,'w'))




# QueuingPolicy: This class is used to enforce the queuing policy in the
# queue directory.  The Queue directory should consist only of links to
# files in other directories.  The link names are formatted beginning
# with the datetime when the item snippet was created.  Feed pubDate is
# either grepped out out the feed or determined from the modification
# date of the feed XML file.
class QueuingPolicy:

  def __init__(self, maxItems = 5000, pastDays = 3650):

    if (maxItems > 5000):
      maxItems = 5000
    self.maxItems = maxItems

    self.pastDays = pastDays


  def enforce(self, dir, rssOutFile):

    # print "maxItems: %d, pastDays: %d" % (self.maxItems, self.pastDays)
    
    now = datetime.datetime.utcnow()
    if os.path.exists(rssOutFile):
      feedPubDate = datetime.datetime.utcfromtimestamp(os.stat(rssOutFile).st_mtime)
    else:
      feedPubDate = datetime.datetime.utcfromtimestamp(0)

    # print "Extracted Pub Date: %s" % feedPubDate.isoformat(' ')
    
    filePairs = [
      (os.path.abspath(dir) + "/" + x,
       datetime.datetime.strptime(x[0:19],"%Y-%m-%d-%H-%M-%S"),
       now - datetime.datetime.strptime(x[0:19],"%Y-%m-%d-%H-%M-%S"))
      for x in os.listdir(dir) ]
    filePairs.sort(cmp = lambda x,y: cmp(y[1], x[1]))

    # print "Items queued: %d" % len(filePairs)

    n = 0;    
    for fileTuple in filePairs:
      n = n + 1
      # print "pubDate: %s" % fileTuple[1].isoformat(' ')
      # print "Days Past: %d" % fileTuple[2].days
      if (((fileTuple[2].days > self.pastDays) or
           (n > self.maxItems)) and
          (fileTuple[1] < feedPubDate)):
        os.unlink(fileTuple[0])

    


# This specializes ConfigParser.ConfigParser class in order to have a
# get() which returns a prescribed value when the option does not exist
# (i.e. dne = <value to return>)
class DatacastingConfigParser(ConfigParser.ConfigParser):
  def get(self, section, option, vars = {}, raw = False, dne = None):
    if ((dne is not None) and
        (not self.has_option(section, option))):
      return dne
    return ConfigParser.ConfigParser.get(self, section, option,
                                         vars = vars, raw = raw)

        
# The following class maintains state between executions of the
# datacasting scripts and is used to enforce uniqueness requirements.
class DatacastingState:
  
  def __init__(self, feedName, feedCfgFile, nItems2Track = 2000):

    self.feedName     = feedName
    self.feedCfgFile  = feedCfgFile
    self.nItems2Track = nItems2Track

    self.nItemsIngested  = 0
    self.itemList        = []
    self.productNameDict = {}
    self.itemGUIDDict    = {}
