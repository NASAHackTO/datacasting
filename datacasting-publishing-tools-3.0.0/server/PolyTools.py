#! /usr/bin/env python

# This module implements polygon simplification of lat/lon polygons
# using great circle computation of distance and bearings.

# Copyright [2010]. California Institute of Technology.  ALL RIGHTS RESERVED.
# U.S. Government sponsorship acknowledged. Any commercial use must be
# negotiated with the Office of Technology Transfer at the California
# Institute of Technology.

# This software is subject to U. S. export control laws and regulations
# (22 C.F.R. 120-130 and 15 C.F.R. 730-774). To the extent that the
# software is subject to U.S. export control laws and regulations, the
# recipient has the responsibility to obtain export licenses or other
# export authority as may be required before exporting such information
# to foreign countries or providing access to foreign nationals.

import sys
import math
import bisect
import GeoTools

# Global debug variables for outputting KML
kml_debug = ''
KML_HEIGHT = 2500000

# This class implents a key queued list.  This is an ordered list that
# presents itself as a queue ordered by a key value.  Each item has an
# associated key which is an integer.  pop_key() from this stack results
# in the item with the highest key value regardless of it's place in the
# item list.
class KeyQueuedList:
  # Initialize internal lists
  def __init__(self):
    self.key_list = []
    self.key_idx_list = []
    self.items = []

  # Return the number of items stored in the list
  def __len__(self):
    return len(self.items)

  # Appending is just inserting at the end
  def append(self, key, item):
    self.insert_item(self.__len__(), key, item)

  # Insert the item in the item list and insert the key in the sorted
  # key stack
  def insertItem(self, i, key, item):
    pos = bisect.bisect(self.key_list, key)
    self.key_list.insert(pos, key)
    self.key_idx_list.insert(pos, item)
    self.items.insert(i, item)

  # Pop the key on top of the key stack (largest key) and pull the item
  # from the item list.  Return the item's index and the item itself.
  def popKey(self):
    key     = self.key_list.pop()
    key_idx = self.key_idx_list.pop()
    i_idx   = self.items.index(key_idx)
    item    = self.items[i_idx]

    del self.items[i_idx]

    return (i_idx, item)

  # Return the value of the key on the top of the key stack
  def maxKey(self):
    return self.key_list[-1]

  # Debug function to dump the keys and other data structure info.
  def __str__(self):
    s =  ( "nkeys: %d, nkeyidxs: %d, nitems: %d, " %
           (len(self.key_list), len(self.key_idx_list), len(self.items)) )
    for i in range(0,len(self.key_list)):
      i_idx = self.items.index(self.key_idx_list[i])
      s += ( "k(%d) %.3f -> %d, " %
             (i, self.key_list[i], i_idx) )

    size = 0
    for item in self.items:
      size += len(item)

    s += ("sum of item lengths: %d" % size)
    return s



# This class stores a line segment along with a split point on which the
# segment can be divided.  This class will be used as the item in the
# queue.
class SplittableLineSegment():
  def __init__(self, idx, line):
    self.splitIdx = idx
    self.line = line

  def __len__(self):
    return len(self.line)

  def __getitem__(self,key):
    return (self.line[key])

  # Return debug info about the segment
  def __str__(self):
    return ("len: %d,  s_idx: %d, 1st: (%.3f, %.3f), last: (%.3f, %.3f)"
            % (len(self.line), self.splitIdx, self.line[0][0], self.line[0][1],
               self.line[-1][0], self.line[-1][1]) )

  # Execute the split and return the resulting lines
  def splitLine(self):
    a = self.line[:self.splitIdx + 1]
    b = self.line[self.splitIdx:]

    return (a,b)

  

# Given a poly-line, this determines which point in the poly-line
# deviates most from the line defined by the first and last point in the
# poly-line and returns the great circle distance from the point to the
# line.
def findLineSplitPoint(line, distFn):
  # If the line is only two points, there is no distance, return 0,0
  if len(line) < 3:
    return (0, 0)

  # Compute the distance from each intermediary point to the simple
  # line.
  dist = [ distFn(line[0], line[-1], line[i])
           for i in range(1, len(line) - 1) ]

  # Get the max distance and index of the max deviating point
  max_dist  = max(dist)
  # Need to add 1 because index doesn't include first item in line
  max_index = dist.index(max_dist) + 1

  return (max_dist, max_index)



#  Extract the line from the list of items.  This is abstracted because
#  the line items are a bit hairy.  Maybe I'll class-ify the items.
def computeOutputLine(lineList_items):
  out_line = ( [ l.line[0] for l in lineList_items ] +
                [ lineList_items[-1].line[-1] ] )

  return out_line



# Debug function to dump the line to stdout
def dumpOutputLine(lineList_items):
  out_line = computeOutputLine(lineList_items)
  print "out line: ",
  for p in out_line:
    print ( "(%.3f, %.3f)" % p),
  print       



# Debug funciton to dump the line as a KML polygon.  This assumes that
# the line that you're simplifying is a polygon with a first and last
# point being the same.
def kmlOutputLine(lineList_items, name):
  out_line = computeOutputLine(lineList_items)
  coordlist = ", ".join([ ("%f, %f, %d" % (p[1], p[0], KML_HEIGHT)) for p in out_line])

  d = {}
  d['coordlist'] = coordlist
  d['name'] = name
  buf = (KML_POLY % d)
  del d

  return buf

def eucDistPt2LinSq(lp1, lp2, p):
  # See distSq computation in: http://ryba4.com/python/ramer-douglas-peucker
  a = (p[0] - lp1[0], p[1] - lp1[1])
  b = (lp2[0] - lp1[0], lp2[1] - lp1[1])

  # Degenerate case where the line is actually zero length
  if (b == (0,0)):
    return (a[0]**2 + a[1]**2)
  
  return ( (a[0]**2 + a[1]**2) - ( (a[0] * b[0] + a[1] * b[1]) /
                                   (b[0]**2 + b[1]**2) ) )

  
def ramerDouglasStough(line, dist_thresh, max_points, distFn = eucDistPt2LinSq,
                            dbg = False, kml = False):
  # This function implements the Ramer-Douglas-Peucker algorithm as
  # described in:
  #
  #  http://ryba4.com/python/ramer-douglas-peucker
  #
  
  # With a twist...  First, all points are assumed to be (lat, lon) and
  # all distances are computed on the great circle.  Next, we take a
  # line, distance threshold, AND max number of points in the resulting
  # reduced line.  Rather than a recursive implementation, this is a
  # greedy algorithm which keeps a list of line segments to operate on.
  # It chooses the line segment with the greatest deviant point to
  # divide next.  If there are no segments exceeding the threshold, we
  # complete.  If our output line will have the max number of points, we
  # complete.  With unlimited points, it should be the same as the
  # original algorithm.  With limited points, it should essentially end
  # up setting the dist thresh to the appropriate value.

  if kml:
    global kml_debug
    kml_debug = ''

  # We're using a KeyQueuedList of the split point and line segment
  # keyed off of the deviation and queued to return max distance.
  lineList = KeyQueuedList()

  # Initialize the list with the whole line.  Note: items are made up of
  # a tuple containing the max_index (split point) and the line.
  (max_dist, max_index) = findLineSplitPoint(line, distFn)

  item = SplittableLineSegment(max_index, line)
  lineList.insertItem(0, max_dist, item)

  # If our max deviation is > the threshold and we have fewer than
  # max_points, keep working.  If the poly-line is irriducable then we
  # will end up with a list of two point segments which all have the
  # deviance of 0.
  iteration = 0
  while ((lineList.maxKey() > dist_thresh) and
         ((len(lineList) + 1) < max_points)):

    if dbg:
      print "  max key: %.3f" % lineList.maxKey()
      print "list dump: %s" % lineList
      dumpOutputLine(lineList.items)

    # Pop the top key/item and unpack the item into idx (split point)
    # and line
    (key_idx, line_item) = lineList.popKey()
    idx = line_item.splitIdx
    line = line_item.line

    (line_a, line_b) = line_item.splitLine()

    if dbg:
      print "Popped: key_idx: %d" % key_idx
      print ("  line: %s" % line_item )

    # We're splitting this line into two segments, line_a and line_b.
    # For each a and b, find the max point and its index.  Then, insert
    # each segment back into the list at the same place we popped.
    (a_max_dist, a_max_idx) = findLineSplitPoint(line_a, distFn)
    item = SplittableLineSegment(a_max_idx, line_a)
    a_idx = key_idx
    lineList.insertItem(a_idx, a_max_dist, item)
    if dbg:
      print ("  line_a: %s" % item )

    # Note that the first point in b is the same as the last point in
    # a.  Line segment b gets inserted at key_idx + 1 so it will be next
    # to a.
    (b_max_dist, b_max_idx) = findLineSplitPoint(line_b, distFn)
    item = SplittableLineSegment(b_max_idx, line_b)
    b_idx = key_idx + 1
    lineList.insertItem(b_idx, b_max_dist, item)
    if dbg:
      print ("  line_b: %s" % item )

    if kml:
      kml_debug = kml_debug + kmlOutputLine(lineList.items,
                                              'Iteration %d' % iteration)

    iteration = iteration + 1
      
  # Once we've completed the iteration, the final line is extracted by
  # taking the first point of every segment and the last point of the
  # last segment.  This works because the last point in each segment is
  # the first in the next.
  out_line = computeOutputLine(lineList.items)

  # If we happen to output a line of max points notify the user of the
  # effective distance threshold.
  if len(out_line) == max_points:
    print ("NOTICE: max_points reached, effective dist threshold: %f" %
           lineList.maxKey())

  return out_line



# Load a poly-line from a single line file of space-separated lat/lon
# pairs.
def loadLineFromFile(fname):
  rawLines = file(fname,'r').readlines()

  rawCoords = rawLines[0].strip().split()
  listLatLon = [ (float(rawCoords[i]), float(rawCoords[i+1]))
                 for i in range(0, len(rawCoords), 2) ]

  return listLatLon



# Using a polygon.txt, and the hard-coded parameters below, simplify the
# polygon while dumping debug info and an "output.kml" file with
# initial, intermediate, and final results
def test():
  dist_thresh = 5.0 # km
  max_points  = 512
  global kml_debug
  
  line = loadLineFromFile('polygon.txt')

  # Generate KML of initial polygon
  coordlist = ", ".join([ ("%f, %f, %d" % (p[1], p[0], KML_HEIGHT)) for p in line])
  d = {}
  d['coordlist'] = coordlist
  d['name'] = 'Initial Polygon'
  buf = (KML_POLY % d)
  del d

  # Simplify polygon as a poly line
  out_line = ramerDouglasStough(line, dist_thresh, max_points, GeoTools.gcDistXtrack,
                                dbg = True, kml = True)

  # When kml output is turned on, KML accumulates in the kml_debug
  # string.  Grab it.
  buf = buf + kml_debug

  # Generate KML of final polygon
  coordlist = ", ".join([ ("%f, %f, %d" % (p[1], p[0], KML_HEIGHT)) for p in out_line])
  d = {}
  d['coordlist'] = coordlist
  d['name'] = 'Final Polygon'
  buf = buf +  (KML_POLY % d)
  del d

  # Dump information about final line simplification...
  print ( "Orig line len: %s, Final line len: %s, Dist thresh: %.3f, Max points %d" %
          (len(line), len(out_line), dist_thresh, max_points) )
  print "Out line: ",
  for p in out_line:
    print ( "(%.3f %.3f)" % p),
  print

  # Dump the KML output to a file
  f = file("output.kml", 'w')
  f.write(KML_HEADER)
  f.write(buf)
  f.write(KML_FOOTER)
  f.close()



# Templates for KML Generation
KML_HEADER = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
	<name>KmlFile</name>
	<StyleMap id="msn_ylw-pushpin">
		<Pair>
			<key>normal</key>
			<styleUrl>#sn_ylw-pushpin</styleUrl>
		</Pair>
		<Pair>
			<key>highlight</key>
			<styleUrl>#sh_ylw-pushpin</styleUrl>
		</Pair>
	</StyleMap>
	<Style id="sh_ylw-pushpin">
		<IconStyle>
			<scale>1.3</scale>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
			</Icon>
			<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
		</IconStyle>
		<LineStyle>
			<color>ff1410ff</color>
			<width>2</width>
		</LineStyle>
		<PolyStyle>
			<fill>0</fill>
		</PolyStyle>
	</Style>
	<Style id="sn_ylw-pushpin">
		<IconStyle>
			<scale>1.1</scale>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
			</Icon>
			<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
		</IconStyle>
		<LineStyle>
			<color>ff1410ff</color>
			<width>2</width>
		</LineStyle>
		<PolyStyle>
			<fill>0</fill>
		</PolyStyle>
	</Style>
'''

# coordinates are in comma separated triplets of lat lon height:
#
#    name = <string>
#    coordlist = "lat1, lon1, h1, lat2, lon2, h2, ... latn, lonn, hn"
KML_POLY = '''<Placemark>
		<name>%(name)s</name>
		<styleUrl>#msn_ylw-pushpin</styleUrl>
		<Polygon>
			<altitudeMode>relativeToGround</altitudeMode>
			<outerBoundaryIs>
				<LinearRing>
					<coordinates>%(coordlist)s</coordinates>
				</LinearRing>
			</outerBoundaryIs>
		</Polygon>
	</Placemark>
'''

KML_FOOTER = '''</Document>
</kml>
'''

if (__name__ == "__main__"):
  print 'executing test()'
  test()
  print 'completed test()'
