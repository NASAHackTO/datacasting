# This module implements lat/lon distances and bearings using great
# circle computation.

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

# Global variable definitions
R_earth = 6371.0                                        # Mean radius in km
DEG2RAD = math.pi / 180.0                               # Convert deg to rad
RAD2DEG = 180.0 / math.pi                               # Convert rad to deg

# Given two points, return the bearing between them in degrees.
#  
# see: http://www.movable-type.co.uk/scripts/latlong.html
#
def brngToDeg(p1, p2):
  lat1 = p1[0] * DEG2RAD
  lon1 = p1[1] * DEG2RAD
  lat2 = p2[0] * DEG2RAD
  lon2 = p2[1] * DEG2RAD
  dLon = lon2 - lon1

  y = math.sin(dLon) * math.cos(lat2)
  x = (math.cos(lat1) * math.sin(lat2) -
       (math.sin(lat1) * math.cos(lat2) * math.cos(dLon)))

  b = math.atan2(y, x) * RAD2DEG

  return b

                                

# This function implements the spherical law of cosines great circle
# distance between two points.
#
# see: http://www.movable-type.co.uk/scripts/latlong.html
#
def gcDist(p1, p2):
  lat1 = p1[0] * DEG2RAD
  lon1 = p1[1] * DEG2RAD
  lat2 = p2[0] * DEG2RAD
  lon2 = p2[1] * DEG2RAD

  d = math.acos(math.sin(lat1) * math.sin(lat2) +
                math.cos(lat1) * math.cos(lat2) *
                math.cos(lon2 - lon1)) * R_earth

  return d


       
# This function implents the cross-track distance between the point, p,
# and the line defined by lp1 and lp2.
#  
# see: http://www.movable-type.co.uk/scripts/latlong.html
#      
def gcDistXtrack(lp1, lp2, p):
  d13 = gcDist(lp1, p)

  # In the case of polygon point reduction, our base case has the two
  # end points being identical.  This leads to a degenrate line which
  # has no bearing, so we detect and return distance.
  if (lp1 == lp2):
    return d13
  else:  
    brng13 = brngToDeg(lp1, p) * DEG2RAD
    
    brng12 = brngToDeg(lp1, lp2) * DEG2RAD

    dxt = (math.asin(math.sin(d13/R_earth) *
                      math.sin(brng13 - brng12)) * R_earth)

    # The cross track distance is signed based on what side of the line
    # you're on, so, we return the abs().
    return abs(dxt)



