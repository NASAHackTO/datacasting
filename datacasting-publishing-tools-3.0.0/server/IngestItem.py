#! /usr/bin/env python

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

import PyRSS2Gen
import DatacastingGen


import os
import os.path
import sys
import getopt
import datetime
import ConfigParser

def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:],
                               "c:d:eho:v",
                               ["config=", "dir=", "erase", "help", "output=",
                                "verbose"])
  except getopt.GetoptError:
    # print help information and exit:
    usage()
    sys.exit(2)
    
  # Set initial values...
  output     = None
  dirMode    = False
  eraseItems = False
  verbose    = False
  showUsage  = False
  configFile = "./config.cfg"
  # Process opts
  for o, a in opts:
    if o in ("-c", "--config"):
      configFile = a
    if o in ("-d", "--dir"):
      dirMode = True
      dir = a
    if o in ("-h", "--help"):
      usage()
      sys.exit()
    if o in ("-o", "--output"):
      output = a
    if o in ("-e", "--erase"):
      eraseItems = True
    if o in ("-v", "--verboes"):
      verbose = True

  # Did we get called with proper agruments?
  if (not dirMode and len(args) == 0):
    usage()
    sys.exit()
    

  # Read in config file information
  if not os.path.lexists(configFile):
    print "ERROR: Can't find config file, exiting in shame.  No items ingested."
    sys.exit()

  cp = DatacastingGen.DatacastingConfigParser()
  cp.read(configFile)

  # Extract necessary variables from config file
  # Get feed level info; needed to deal with custom elements
  rss            = DatacastingGen.Feed.FromConfig(cp)

  # itemSource: if present it needs a Source() object 
  isTuple        = eval(cp.get('Item','itemsource',
                               dne = 'None'))
  if isTuple is not None:
    itemSource   = PyRSS2Gen.Source(isTuple[0], isTuple[1])
  else:
    itemSource   = None
  itemLink       = eval(cp.get('Item','itemlink',
                        dne = 'None'))
  itemPathRoot   = eval(cp.get('Generation', 'itempathroot'))
  queueDirectory = eval(cp.get('Generation', 'queuedirectory'))
  configDict = {}
  configDict['simplifyPolygons'] = eval(cp.get('Item/Extents',
                                               'simplifyPolygons',
                                               dne = 'False'))
  configDict['polyMaxPoints'] = eval(cp.get('Item/Extents',
                                            'polyMaxPoints',
                                            dne = '256'))
  configDict['polyDistThresh'] = eval(cp.get('Item/Extents',
                                             'polyDistThresh',
                                             dne = '5.0'))
  
  
  if dirMode:
    fileList = [ os.path.abspath(dir) + "/" + x
                 for x in os.listdir(dir) ]
  else:
    fileList = [ os.path.abspath(x) for x in args ]
    

  # DEBUG
  # print "Item files processed: %d" % len(fileList)
  
  for file in fileList:
    try:
      item = DatacastingGen.Item(txtFileName = file,
                                 source = itemSource,
                                 link = itemLink,
                                 parentFeed = rss,
                                 addlConfig = configDict)


      # Twiddle the guid to match the enclosure + a filename....
      enc = None
      if item.enclosure is not None:
        if item.enclosureList is not [] :
          enc = item.enclosureList[0]
        else:
          enc = item.enclosure

      if enc is not None:  
        item.guid = PyRSS2Gen.Guid(enc.url + "?file=" + file)

      basename = os.path.basename(file)
      (filebase, ext) = os.path.splitext(basename)

      # Store the item in a hierarchical directory structure.  If needed
      # subdirectories don't exist, create them.
      if item.pubDate is not None:
        pd = item.pubDate
      else:
        pd = datetime.datetime.utcnow()
      itemOutputPath = (itemPathRoot + "/" +
                        "%04d/" % pd.year +
                        ("%02d-%02d" % (pd.month, pd.day)))
      if not os.path.lexists(itemOutputPath):
        os.makedirs(itemOutputPath)

      # Save off the XML snippet
      outXMLName = os.path.abspath(itemOutputPath +
                                   ("/%02d-%02d-%02d-" %
                                    (pd.hour, pd.minute, pd.second)) +
                                   basename + ".xml")
      if (verbose and os.path.lexists(outXMLName)):
        print "WARNING: Overwriting %s" % outXMLName
      item.SaveXML(outXMLName)

      # DEBUG
      # print "outXMLName: %s" % outXMLName

      # Link the created item into the queuing directory
      fullQueuedPath = os.path.abspath(queueDirectory +
                                       ("/%04d-%02d-%02d-%02d-%02d-%02d-" %
                                        (pd.year, pd.month, pd.day,
                                         pd.hour, pd.minute, pd.second)) +
                                       basename + ".xml")
      if not os.path.lexists(queueDirectory):
        os.makedirs(queueDirectory)
      if os.path.lexists(fullQueuedPath):
        if verbose:
          print "WARNING: Requeuing %s" % fullQueuedPath
        os.unlink(fullQueuedPath)
      os.symlink(outXMLName, fullQueuedPath)
      
    except Exception, inst:
      print "WARNING: Item text file ingestion failed..."
      print "  Item file name:  %s" % file
      print "  Exception: %s" % inst
      print "  Continuing processing."
      raise


  if eraseItems:
    for file in fileList:
      try:
        os.unlink(file)
      except Exception, inst:
        print "Could not unlink: %s" % file
        print "Exception: %s" % inst


def usage():
  print """
  IngestItem.py [options] <item file(s)>
  
    -c, --config=<config_file>
        Load the feed configuration from the named file.  This supports
        multiple feeds; simply create a config file for each data feed and
        name that config file when you ingest items.
  
    -e, --erase
        Erase input item file after processing.
        
    -d, --dir=<dir_name>
        Process all the files in the named directory as item files.

    -v, --verbose
        Output any status info.  This includes warnings of file over
        writings that may be accidental and cause loss of feed items.
  """
  
  
if (__name__ == "__main__"):
  # print 'executing main()'
  main()
  # print 'completed main()'
