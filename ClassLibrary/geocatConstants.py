"""
    swisstopo geocat constants
    this constant values use often in some project
"""

from pathlib import Path

def __getProxyDict(*args):
    """ :proxyDict: define the proxys - when you do the modification on a private laptop in a private WIFI, you don't need that. 
    It is necessary when you run the script with VPN or directly in Wabern """
    return {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}
proxyDict = __getProxyDict()

def __getDevProxyDict(*args):
    """ :proxyDict: define the proxys - when you do the modification on a private laptop in a private WIFI, you don't need that. 
    It is necessary when you run the script with VPN or directly in Wabern """
    return {"http": "proxy-bvcol.admin.ch:8080", "https": "proxy-bvcol.admin.ch:8080"}
devProxyDict = __getDevProxyDict()

def __getEnvironmentDict(*args):
    """ two possible environments INT or PROD"""
    return {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
environmentDict = __getEnvironmentDict()

def __getEnvironmentList(*args):
    """ need to build the environment radioButtons on geocatLoginGUI """
    return ["INT", "PROD"]
environmentList = __getEnvironmentList()

def __getDataSourceList(*args):
    """ need to build the dataSource radioButtons on geocatLoginGUI """
    return ["API3", "BMD", "BOD"]
dataSourceList = __getDataSourceList()

def getBackupModeList(*args):
    """ need to build the backupMode radioButtons on geocatLoginGUI """
    return ["None", "Backup", "Restore"]
backupModeList = getBackupModeList()

def getBatchEditModeDict(*args):
    return {"ADD": "add", "DELETE": "delete", "REMOVE": "delete", "REPLACE": "replace"}
batchEditModeDict = getBatchEditModeDict()

def getBatchEditModeList(*args):
    """ need to build the batcheditMode radioButtons on geocatLoginGUI """
    return ["ADD", "DELETE", "REMOVE", "REPLACE"]
batchEditModeList = getBatchEditModeList()

def getLanguageDict(*args):
    return {"ger": "DE", "fre": "FR", "eng": "EN", "ita": "IT"}
languageDict = getLanguageDict()

def getCategoryDict(*args):
    return {"Default": 1, "five_not_to_monitor": 38749882, "Testdatensatz": 42508195, "veraltet / obsolet": 42508194}
categoryDict = getCategoryDict()

def getLanguagesSufixList(*args):
    """  """
    return ["_de", "_fr", "_it", "_en", "_rm"]
languagesSufixList = getLanguagesSufixList()

def getKeywordsList(*args):
    """ need to build the keyword combobox on geocatLoginGUI """
    return ["BGDI Bundesgeodaten-Infrastruktur", "opendata.swiss"]
keywordsList = getKeywordsList()

def getProtocolsList(*args):
    """ need to build the protocol combobox on geocatLoginGUI """
    return ["ESRI:REST", "OPENDATA:SWISS", "WWW:DOWNLOAD-URL", "WWW:DOWNLOAD-APP"]
protocolsList = getProtocolsList()

def getSearchFilter(*args):
    return "&facet.q="
searchFilter = getSearchFilter()

def getPlus(*args):
    return "%26"
plus = getPlus()

def getGroupOwner(*args):
    return "groupOwner%2F"
groupOwner = getGroupOwner()

def getIsNotHarvested(*args):
    return "isHarvested%2Fn"
notHarvested = getIsNotHarvested() # deprecated
isNotHarvested = getIsNotHarvested()

def getIsGeoBasicDataFederal(*args):
    return "type%2Fbasicgeodata-federal"
isGeoBasicDataFederal = getIsGeoBasicDataFederal()

def getIsGeoBasicDataCantonal(*args):
    return "type%2Fbasicgeodata-cantonal"
isGeoBasicDataCantonal = getIsGeoBasicDataCantonal()

def getIsGeoBasicDataCommunal(*args):
    return "type%2Fbasicgeodata-communal"
isGeoBasicDataCommunal = getIsGeoBasicDataCommunal()

def getIsGeoBasicDataOther(*args):
    return "type%2Fbasicgeodata-other"
isGeoBasicDataOther = getIsGeoBasicDataOther()

def getIsMetadataType(*args):
    return "metadataType%2Fn"
isMetadataType = getIsMetadataType()

def getIsValid(*args):
    return "isValid%2F1"
isValid = getIsValid()

def getIsNotValid(*args):
    return "isValid%2F0"
isNotValid = getIsNotValid()

def getCantonalCodes(*args):
    return ['ag', 'ar', 'ai', 'bl', 'bs', 'be', 'fr', 'ge', 'gl', 'gr', 'ju', 'lu', 'ne', 'nw', 'ow', 'sg', 'sh', 'sz', 'so', 'tg', 'ti', 'ur', 'vd', 'vs', 'zg', 'zh']
cantonalCodes = getCantonalCodes()

def getBackupPath(*args):
    return Path("Q:/logFiles/Backups/")
backupPath = getBackupPath()

# NameSpaces to define the prefixes in the xml-tags
def getNs(*args):
    return {'che': 'http://www.geocat.ch/2008/che', 'gmd': 'http://www.isotc211.org/2005/gmd', 'srv': 'http://www.isotc211.org/2005/srv', 'gco': 'http://www.isotc211.org/2005/gco',
             'xsi': 'http://www.w3.org/2001/XMLSchema-instance', 'xlink': 'http://www.w3.org/1999/xlink', 'gml': 'http://www.opengis.net/gml/3.2', 'gsr': 'http://www.isotc211.org/2005/gsr',
             'gts': 'http://www.isotc211.org/2005/gts', 'gmi': 'http://www.isotc211.org/2005/gmi', 'gmx': 'http://www.isotc211.org/2005/gmx'}
ns = getNs()

def getNamespaces(*args):
    return "xmlns:che='http://www.geocat.ch/2008/che' xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:srv='http://www.isotc211.org/2005/srv' xmlns:gco='http://www.isotc211.org/2005/gco' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:gml='http://www.opengis.net/gml/3.2' xmlns:gsr='http://www.isotc211.org/2005/gsr' xmlns:gts='http://www.isotc211.org/2005/gts' xmlns:gmi='http://www.isotc211.org/2005/gmi' xmlns:gmx='http://www.isotc211.org/2005/gmx'"
namespaces = getNamespaces()

odsLink = "https://opendata.swiss/"
odsSearchIdentifierUrlPrefix = "https://opendata.swiss/api/3/action/package_search?q=identifier:"

restFulApiUrlPrefix = "https://api3.geo.admin.ch/rest/services/api/MapServer/"

api3RequestUrl = "https://api3.geo.admin.ch/rest/services/api/MapServer"

bmdRequestUrl = "https://ltbmd.adr.admin.ch/BmdService/Read/SqlInDataBase?statement=select distinct geocatuuid as idGeoCat, techpublayername as layerBodId, ingeststate from bmd.PubLayer where geocatuuid <> '' and geocatuuid <> '-' and ingeststate = 'Productive'&format=json"

#-----------------------------------------------------------------------------------------------------
# Kt. BS only

def __getValuesToChange(*args):
    return {"shop.geo.bs.ch": "WWW:DOWNLOAD-APP", "map.geo.bs.ch": "CHTOPO:specialised-geoportal"}
valuesToChange = __getValuesToChange()