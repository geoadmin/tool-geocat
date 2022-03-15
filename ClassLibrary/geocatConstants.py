"""
swisstopo geocat constants
this constant values use often in some project
"""
def getProxyDict(*args):
    """ :proxyDict: define the proxys - when you do the modification on a private laptop in a private WIFI, you don't need that. 
    It is necessary when you run the script with VPN or directly in Wabern """
    return {"http": "prp03.admin.ch:8080", "https": "prp03.admin.ch:8080"}
proxyDict = getProxyDict()

def getEnvironmentDict(*args):
    """ two possible environments INT or PROD"""
    return {"INT": "https://geocat-int.dev.bgdi.ch/geonetwork/srv/", "PROD": "https://www.geocat.ch/geonetwork/srv/"}
environmentDict = getEnvironmentDict()

def getEnvironmentList(*args):
    """ need to build the environment radioButtons on geocatLoginGUI """
    return ["INT", "PROD"]
environmentList = getEnvironmentList()

def getDataSourceList(*args):
    """ need to build the dataSource radioButtons on geocatLoginGUI """
    return ["API3", "BMD", "BOD"]
dataSourceList = getDataSourceList()

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

def getKeywordsList(*args):
    """ need to build the keyword combobox on geocatLoginGUI """
    return ["BGDI Bundesgeodaten-Infrastruktur", "opendata.swiss"]
keywordsList = getKeywordsList()

def getProtocolsList(*args):
    """ need to build the protocol combobox on geocatLoginGUI """
    return ["ESRI:REST", "OPENDATA:SWISS"]
protocolsList = getProtocolsList()

def getIsNotHarvested(*args):
    return "&facet.q=isHarvested%2Fn"
notHarvested = getIsNotHarvested() # deprecated
isNotHarvested = getIsNotHarvested()

def getIsMetadataType(*args):
    return "%26metadataType%2Fn"
isMetadataType = getIsMetadataType()

def getIsValid(*args):
    return "%26isValid%2F1"
isValid = getIsValid()

def getIsNotValid(*args):
    return "%26isValid%2F0"
isNotValid = getIsNotValid()

# NameSpaces to define the prefixes in the xml-tags
def getNs(*args):
    return {'gmd': 'http://www.isotc211.org/2005/gmd', 'gmx': 'http://www.isotc211.org/2005/gmx', 'gco': 'http://www.isotc211.org/2005/gco', 'che': 'http://www.geocat.ch/2008/che'}
ns = getNs()

def getNamespaces(*args):
    return "xmlns:che='http://www.geocat.ch/2008/che' xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:srv='http://www.isotc211.org/2005/srv' xmlns:gco='http://www.isotc211.org/2005/gco' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:gml='http://www.opengis.net/gml/3.2' xmlns:gsr='http://www.isotc211.org/2005/gsr' xmlns:gts='http://www.isotc211.org/2005/gts' xmlns:gmi='http://www.isotc211.org/2005/gmi' xmlns:gmx='http://www.isotc211.org/2005/gmx'"
namespaces = getNamespaces()

odsLink = "https://opendata.swiss/"
odsSearchIdentifierUrlPrefix = "https://opendata.swiss/api/3/action/package_search?q=identifier:"

restFulApiUrlPrefix = "https://api3.geo.admin.ch/rest/services/api/MapServer/"

api3RequestUrl = "https://api3.geo.admin.ch/rest/services/api/MapServer"

bmdRequestUrl = "https://ltbmd.adr.admin.ch/BmdService/Read/SqlInDataBase?statement=select distinct geocatuuid as idGeoCat, techpublayername as layerBodId, ingeststate from bmd.PubLayer where geocatuuid <> '' and geocatuuid <> '-' and ingeststate = 'Productive'&format=json"

# XML-Categories from geocat.ch
x_start = "{http://www.geocat.ch/2008/che}CHE_MD_Metadata"
x_char = "{http://www.isotc211.org/2005/gco}CharacterString"
x_form = "{http://www.isotc211.org/2005/gmd}MD_Format"
x_name = "{http://www.isotc211.org/2005/gmd}name"
x_vers = "{http://www.isotc211.org/2005/gmd}version"
x_org = "{http://www.isotc211.org/2005/gmd}organisationName"
x_fname = "{http://www.geocat.ch/2008/che}individualFirstName"
x_lname = "{http://www.geocat.ch/2008/che}individualLastName"
x_idinf = "{http://www.isotc211.org/2005/gmd}identificationInfo"
x_data_id = "{http://www.geocat.ch/2008/che}CHE_MD_DataIdentification"
x_cit = "{http://www.isotc211.org/2005/gmd}citation"
x_cicit = "{http://www.isotc211.org/2005/gmd}CI_Citation"
x_tit = "{http://www.isotc211.org/2005/gmd}title"
x_pttxt = "{http://www.isotc211.org/2005/gmd}PT_FreeText"
x_txt = "{http://www.isotc211.org/2005/gmd}textGroup"
x_loc = "{http://www.isotc211.org/2005/gmd}LocalisedCharacterString"
x_lan = "{http://www.isotc211.org/2005/gmd}language"
x_lanc = "{http://www.isotc211.org/2005/gmd}LanguageCode"
x_srv1 = "{http://www.geocat.ch/2008/che}CHE_SV_ServiceIdentification"
x_srv2 = "{http://www.isotc211.org/2005/srv}SV_ServiceIdentification"
x_kws = "{http://www.isotc211.org/2005/gmd}MD_Keywords"
x_kwd = "{http://www.isotc211.org/2005/gmd}keyword"
x_ext = "{http://www.isotc211.org/2005/gmd}EX_Extent"
x_ptloc = "{http://www.isotc211.org/2005/gmd}PT_Locale"
x_mail = "{http://www.isotc211.org/2005/gmd}electronicMailAddress"
x_role = "{http://www.isotc211.org/2005/gmd}CI_RoleCode"
x_mdcon = "{http://www.isotc211.org/2005/gmd}contact"
x_rescon = "{http://www.isotc211.org/2005/gmd}pointOfContact"
x_discon = "{http://www.isotc211.org/2005/gmd}distributorContact"
x_desc = "{http://www.isotc211.org/2005/gmd}description"

x_datacon = "{http://www.isotc211.org/2005/gmd}pointOfContact"
x_discon = "{http://www.isotc211.org/2005/gmd}distributorContact"
