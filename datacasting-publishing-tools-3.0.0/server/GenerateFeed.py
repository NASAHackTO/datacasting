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

import datetime
import PyRSS2Gen
import DatacastingGen

import os
import os.path
import sys
import getopt
import ConfigParser

def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:],
                               "c:ho:v",
                               ["config=", "help", "output=", "verbose"])
  except getopt.GetoptError:
    # print help information and exit:
    usage()
    sys.exit(2)
    
  # Set initial values...
  output  = None
  dirMode = False
  verbose = False
  configFile = "./config.cfg"
  # Process opts

  for o, a in opts:
    if o in ("-c", "--config"):
      configFile = a
    if o == "-v":
      verbose = True
    if o in ("-h", "--help"):
      usage()
      sys.exit()
    if o in ("-o", "--output"):
      output = a

  # Read in config file information
  if not os.path.lexists(configFile):
    print ("ERROR: Can't find config file, exiting in shame.  " +
           "Feed not generated.")
    usage()
    sys.exit()

  cp = DatacastingGen.DatacastingConfigParser()
  cp.read(configFile)
  
  # Extract necessary variables from config file
  rss            = DatacastingGen.Feed.FromConfig(cp)
  rssOutputFile  = eval(cp.get('Generation', 'rssoutputfile'))
  queueDirectory = eval(cp.get('Generation', 'queuedirectory'))
  xmlLint        = eval(cp.get('Generation', 'useXmllint', dne = "True"))
  if cp.has_section('QueuePolicy'):
    policy = DatacastingGen.QueuingPolicy(
      maxItems = eval(cp.get('QueuePolicy', 'maxitems', dne = '5000')),
      pastDays = eval(cp.get('QueuePolicy', 'pastdays', dne = '3650')))
  else:
    policy = DatacastingGen.QueuingPolicy()

  rssOutputPath = os.path.abspath(rssOutputFile)

  policy.enforce(queueDirectory, rssOutputPath)

  fileList = [ os.path.abspath(queueDirectory) + "/" + x
               for x in os.listdir(queueDirectory) ]
  importedItems = []
  for file in fileList:
    try:
      if file.endswith(".xml"):
        importedItems.append(DatacastingGen.Item(xmlFileName = file))
    except Exception, inst:
      print "ERROR: Failed to import XML item file from queue."
      print "  Failed on file:  %s" % file
      print "  Exception: %s" % inst
      print "  Item skipped."

  # We are publishing the feed now...
  rss.pubDate = datetime.datetime.utcnow()

  # Set the items
  rss.items = importedItems

  # Format the XML file to be easily readable by human beings.
  if xmlLint:
    try:
      tmpFile = rssOutputPath + "-unformatted"
      rss.SaveXML(tmpFile)
      command = ("xmllint --format --nowarning %s > %s" %
                 (tmpFile, rssOutputPath))
      os.system(command)
      os.unlink(tmpFile)
    except Exception, inst:
      print "WARNING: Failed to reformat wiht xmllint."
      print "  Exception: %s" % inst
      print "  Outputting unformatted file."
      rss.SaveXML(rssOutputPath)
  else:
    rss.SaveXML(rssOutputPath)



def usage():
  print """
  GenerateFeed.py [options]
  
    -c, --config=<config_file>
        Load the feed configuration from the named file.  This supports
        multiple feeds; simply create a config file for each data feed and
        name that config file when you generate the feed.
  """
  
if (__name__ == "__main__"):
  # print 'executing main()'
  main()
  # print 'completed main()'
