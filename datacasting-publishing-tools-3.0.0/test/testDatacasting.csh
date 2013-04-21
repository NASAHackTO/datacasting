#!/bin/csh

# © [2007]. California Institute of Technology.  ALL RIGHTS RESERVED.
# U.S. Government sponsorship acknowledged. Any commercial use must be
# negotiated with the Office of Technology Transfer at the California
# Institute of Technology.

# This software is subject to U. S. export control laws and regulations
# (22 C.F.R. 120-130 and 15 C.F.R. 730-774). To the extent that the
# software is subject to U.S. export control laws and regulations, the
# recipient has the responsibility to obtain export licenses or other
# export authority as may be required before exporting such information
# to foreign countries or providing access to foreign nationals.

echo "Created link to config.cfg..."
ln -sf ../server/config-sample.cfg config.cfg

# Datacasting Feeds are published in a two step process:
#
# 1) An item or items describiing newly available data are ingested and
#    converted from a simple text format to snippets of XML.  When
#    ingested, these items are immediately linked into a queue directory
#    to be published.
#
# 2) The GenerateFeed script removes old items from the queue if
#    necessary (the queuing policy is controlled by the config.cfg file)
#    and then it publishes all the articles remaining in the queue to an
#    xml file (MODIS_A-gen.xml in this example).

# Both IngestItem and GenerateFeed are configured by the config.cfg
# file.  By default the config.cfg file is looked for in the current
# directory.  You can have multiple feeds by referring to a specific
# file using -c option on the command-line of both IngestItem and
# Generate Feed.

# First you need to ingest the items that will appear in the feed.  You
# can ingest items one at a time or en masse.  Once ingested the items
# will be stored as XML in "items-xml" directory and soft linked from
# the "queue" directory.  Both these directory names can be specified as
# full or relative paths in the config file; for multiple feeds, you
# need an xml directory and a queue directory for each feed.  Item files
# can be deleted after they are ingested once, but there is no harm in
# ingesting them multiple times as they just overwrite the older items.
IngestItem.py items/*.*

# Check out the command-line parameters of IngestItem using:
#  IngestItem.py -h

# Next, GenerateFeed is run to maintain the queue and publish the
# articles remaining in the queue.  In this example, generate feed is
# run immediately after ingesting all the items.  In a real
# installation, you may want to ingest items as they arrive and generate
# the feed every so often (maybe every hour).  This is no problem.  The
# queuing scheme prevents the publishing of partial articles.
GenerateFeed.py

# Check out the command-line parameters of GenerateFeed using:
#  GenerateFeed.py -h


echo ""
echo "Test complete.  A successful test should have produced two"
echo "subdirectories (items-xml and queue) and one file (MODIS_A-gen.xml)"
echo "in the current directory.  The items-xml should contain the XML for"
echo "the items in subdirectories named by the publish year and month."
echo "The queue directory points to all items in items-xml which meet the"
echo "queuing criteria.  Finally the MODIS_A-gen.xml file contains the feed."
echo ""
echo "If you got an error on xmllint, you may need to set useXmllint to"
echo "False in your config file if you don't have xmllint avaliable on your"
echo "system."
echo ""
echo "The Datacasting Server Tools were designed to work with"
echo "Python 2.5 and may work with version 2.4 but will not work with" 
echo "Python 2.3.x or earlier."
echo ""
echo "Your Python version is:"
python -V
echo ""
