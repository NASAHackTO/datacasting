********************************************************************
*** Datacasting Publishing Tools README.txt
********************************************************************

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

This package contains the Datacasting Publishing Tools.  Before using
the tools, please source the setup.csh in your shell.  This adds the
tools to your PATH and sets up the PYTHONPATH so that the tools can find
the PyRSS2Gen module.  You must be in the same directory at the time you
source it to ensure that the paths are correct.

Once the path is setup, you can go to the ./test directory and run the
test.  This not only checks to see if Datacasting will work on your
system, it also demonstrates how to use the tools.  Take a look at the
comments in test/testDatacasting.csh, they explain the usage of the two
publishing scripts.  Although this example calls IngestItem.py and
GenerateFeed.py at the same time, you can run them asynchronously.

Another option for using the Tools is to run the make-executables
script.  First, source the setup.csh to set your environment variables.
Then, run ./make-executables.  This will create small, relocatable
scripts which you can place anywhere in your path to run the Datacasting
Publishing Tools.  These scripts require no additional paths or
environment variable; therefor there is no need to run the setup.csh in
order to use these scripts once they are created.

The Datacasting Publishing Tools were designed to work with Python
2.5 and may work with version 2.4 but will not work with Python 2.3.x or
earlier.

-------------------------------------
    ./server/LoopItems.py Script: WARNING!!!

      This script is intended for testing purposes only.  It will take a
      large pool of item .txt files and produce a never ending feed of
      items which repeates the items in order.  Each published item will
      have a unique GUID reflecting the time it was RE-published as well
      as a pubDate of 'utcnow()'.  This script will run in an infinite
      loop until killed.

      THIS SCRIPT WILL NOT AND IS NOT INTENDED TO PUBLISH NORMAL
      DATACASTING FEEDS.  IT IS USED ONLY TO LOAD TEST THE CLIENT AND
      THE FEED GENERATING SCRIPTS.
-------------------------------------

SUGGESTED USE

At the moment, the error trapping within the Tools is minimal.  In order
to work, the tools need to be able to find the config file and all files
involved need to be formatted as specified in the sample files.

1) Please examine the server/config-sample.cfg file and create your own
   copy tailored to your data.  Remember that you need a config file,
   'item-xml' directory, and 'queue' directory for each feed that you
   intend to publish.  When publishing multiple feeds, you need to use
   the command-line options of both IngestItem and GenerateFeed to point
   the scripts to the config file.

2) When adding newly published data items to the feed, you create text
   files that specify the metadata associated with each new item.  An
   example of this item file is given in server/ref-doc-item.txt.  This
   reference documented item file is fully commented to explain how to
   represent your metadata.  Please read it and be sure to build
   item.txt files that contain as much metadata as you can gather about
   each data item.  The more information that you supply (this includes
   filling as many custom elements as you can) the more useful this feed
   will be to your data consumers.


Example feeds can be found at:

 - http://podaac.jpl.nasa.gov/hurricanes/

 LocalWords:  PYTHONPATH PyRSS Gen corrct
