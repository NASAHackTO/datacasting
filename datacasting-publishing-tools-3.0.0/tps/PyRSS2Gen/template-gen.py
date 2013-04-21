# An example of how to generate a feed by hand.

import datetime
import PyRSS2Gen

rss = PyRSS2Gen.RSS2(
    title = "",
    link = "",
    description = ""
                  "",

    lastBuildDate = datetime.datetime.now(),

    items = [
       PyRSS2Gen.RSSItem(
         title = "",
         link = "",
         description = ""
                       "",
         guid = PyRSS2Gen.Guid(""),
         pubDate = datetime.datetime(2003, 9, 6, 21, 31)),
       PyRSS2Gen.RSSItem(
         title = "",
         link = "",
         description = "",
         guid = PyRSS2Gen.Guid(""),
         pubDate = datetime.datetime(2003, 9, 6, 21, 49)),
    ])

rss.write_xml(open("outfile.xml", "w"))
