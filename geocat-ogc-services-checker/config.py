# GeoCat base URL
HOST = "https://www.geocat.ch"

# URL for retrieving metadata
URL_METADATA = f"{HOST}/geonetwork/srv/eng/catalog.search#/metadata/"

# GeoCat API endpoint for searching metadata
API_SEARCH_URL = f"{HOST}/geonetwork/srv/api/search/records/_search"

OGC_PROTOCOLS = ["OGC:WMS", "OGC:WMTS", "OGC:WFS"]

# HTTP headers for the search request
HEADERS = {
    "Content-Type": "application/json",
    "accept": "application/xml,text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76"
}

# Body for the GeoCat search API request
SEARCH_API_BODY = {
    "from": 0,
    "query": {
        "bool": {
            "must": [
                {
                    "query_string": {
                        "query": "(isPublishedToAll:\"true\")",
                        "default_operator": "AND"
                    }
                }
            ]
        }
    },
    "_source": {
        "includes": [
            "uuid",
            "resourceTitleObject",
            "MD_LegalConstraintsOtherConstraintsObject",
            "contact",
            "contactForResource",
            "contactForDistribution",
            "link"
        ]
    },
    "track_total_hits": True,
    "sort": {"_id": "asc"},
    "size": 3000
}

MAIL_SENDER = "olivier.curdy@swisstopo.ch"

MAIL_SUBJECT = "geocat.ch - Invalid URL in your metadata"

MAIL_BODY_START_TEXT = """
Hello {{name}},

You are receiving this email because you are owner of metadata with invalid URL in the swiss geodata catalogue geocat.ch.

While accessing the following URL, we found some unexpected behaviour.
Please check if those URL are still available and fix them if necessary.

PS: HTTPS or HTTP schema is mandatory for all URL in geocat.ch.

Thank you for your collaboration.
The geocat.ch team

----------

"""

MAIL_BODY_START_HTML = """
<html>
  <body>
    <p>Hello {{name}}<br><br>
        You are receiving this email because you are owner of metadata with invalid URL in the swiss geodata catalogue <a href='https://www.geocat.ch/'>geocat.ch</a>.<br><br>
        While accessing the following URL, we found some unexpected behaviour.<br>
        Please check if those URL are still available and fix them if necessary.<br><br>
        PS: HTTPS or HTTP schema is mandatory for all URL in geocat.ch.<br><br>
       Thank you for your collaboration.<br>
       The geocat.ch team<br><br>
       ----------<br><br>
"""

URL_WHITE_LIST = [
    "^https://map.georessourcen.ethz.ch/$",
    "^https://oereb.llv.li/$",
    "^https://mapplus01/mapplus/fribourg/.*",
    "^http://sparcgis01.ad.net.fr.ch/.*",
    "^https://sparcgis01.ad.net.fr.ch/.*"
]