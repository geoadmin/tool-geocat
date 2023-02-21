GD_SPREADSHEET_ID = "1to10g8bIhVv0GxMQZk00Yc-kIk9FpMzQJp6veFXgN6s"
GD_SHEET_NAME = "Planning%20overview"

GD_SHEET = f"https://docs.google.com/spreadsheets/d/{GD_SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={GD_SHEET_NAME}"

BGDI_GROUP_ID = [
    "69", "51", "53", "25", "41", "52", "40", "27", "37", "39", "38", "8", "34", "6",
    "23", "26", "22", "29125806", "26805108", "13", "36", "50", "19647867"
    ]

WMS_URL = "https://wms.geo.admin.ch/?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities"

WMTS_URL = [
    "https://wmts.geo.admin.ch/EPSG/3857/1.0.0/WMTSCapabilities.xml",
    "https://wmts.geo.admin.ch/1.0.0/WMTSCapabilities.xml",
    "https://wmts.geo.admin.ch/EPSG/21781/1.0.0/WMTSCapabilities.xml",
    "https://wmts.geo.admin.ch/EPSG/4326/1.0.0/WMTSCapabilities.xml"
]

API3_URL = "https://api3.geo.admin.ch/rest/services/api/MapServer"

NS = {
    "wms": "http://www.opengis.net/wms",
    "wmts": "http://www.opengis.net/wmts/1.0",
    "ows": "http://www.opengis.net/ows/1.1"
}