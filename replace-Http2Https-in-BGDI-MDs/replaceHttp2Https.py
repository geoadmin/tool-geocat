
# -*-
'''
------------------------------------------------------------------------------------------------------------------------
Autor:      Reithmeier Martin (rem) in 2021 

Purpose:    This script add one onLine resource with the "Rest-API geo.admin.ch-Link 
            as service to the record with given uuid"

            geocatEnvironment - is defined in module loginWindow
            proxyDict - define the proxys - when you do the modification on a private laptop in a private WIFI, you
                        don't need that. It is necessary when you run the script with VPN or directly in Wabern.

Remarks:    
------------------------------------------------------------------------------------------------------------------------
'''

# import of needed python modules
import sys
# sys.path.append("..\\ClassLibrary") # is needed when use outside from Visual Studio
import xml.etree.ElementTree as ElementTree
import requests
import urllib3
from requests.auth import HTTPBasicAuth
import json
import datetime
import loginWindow as gui
import geocatApiCalls
import geocatConstants as const

# TODO: adapt the following variables
batchName = "replaceHttp2Https"
#editMode = "ADD"
#editMode = "DELETE"
#editMode = "REMOVE"
editMode = "REPLACE"
batchEditMode = const.batchEditModeDict[editMode]
batchEditOperationTag = "<gn_" + batchEditMode + ">"
batchEditOperationCloseTag = "</gn_" + batchEditMode + ">"
keyword = "&keyword=BGDI Bundesgeodaten-Infrastruktur"
protocol = "&protocol=WWW:DOWNLOAD-URL"
searchString = "http://data.geo.admin.ch/"
any = "&any=" + searchString
mainLanguage = "ger"
countOfMDs = ""
timeStamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")

# NameSpaces to define the prefixes in the xml-tags
ns = const.ns
namespaces = const.namespaces

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# function area
#######################################################################################################################################

def writeLog(logValue: str):
    """ write log-informations to file and screen """
    logString = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M.%S%f") + ": " + logValue
    print(logString)
    logFile.write(logString + "\r")

def getDistributionAsRoot(uuid :ElementTree.Element) -> ElementTree.Element:
    """ set the xml_Distribution-Node as root """
    apiSessionCalls.setHeaders("xml")

    urlValue = "api/0.1/records/" + uuid.text
    responsSingleRecord = apiSessionCalls.sendGetRequest(urlValue)
    xmlTreeSingleRecord = ElementTree.fromstring(responsSingleRecord.content)
    return xmlTreeSingleRecord.find(".//gmd:MD_Distribution", ns)

def getGeocatUuids():
    """
    
    """
    writeLog("access the geocat url and count the number of MDs corresponding to the search condition")
    apiRequestCall = geocatApiCalls.geocatRequests(geocatUrlPrefix, geocatUser, geocatPassword)
    geocatResponse = apiRequestCall.sendGetRequest(mainLanguage + "/q?from=1&to=1500" + keyword + protocol + any)
    xmlTreeGeocatResponse = ElementTree.fromstring(geocatResponse.content)
    global countOfMDs
    countOfMDs = xmlTreeGeocatResponse.find("./summary").attrib["count"]
    writeLog("Number of MDs corresponding to your search: " + countOfMDs)
    return ElementTree.fromstring(geocatResponse.content).findall(".//uuid")

def replaceUrl(replaceValue :str, uuid :str):
    """
    :return: the respons of the put request
    """

    apiSessionCalls.setHeaders("json")

    value = "<gn_replace><gmd:URL " + namespaces + ">" + replaceValue + "</gmd:URL></gn_replace>"
    xpath = ".//gmd:transferOptions[" + str(transferOptionsNodeCounter) + "]//gmd:onLine[" + str(onLineNodeCounter) + "]//gmd:linkage"
    writeLog("    value: " + value)
    writeLog("    xpath: " + xpath)

    urlValue  = "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=true"
    return apiSessionCalls.sendPutRequest(urlValue, value, xpath)

def formatResponse(response):
    """
    :return: the message, which has informations for us
    """
    responseJson = response.json()
    metadataErrorsJson = responseJson['metadataErrors']
    metadataInfosJson = responseJson['metadataInfos']
    if len(metadataErrorsJson) == 1:
        errorKeyName = list(metadataErrorsJson.keys())[0]
        message = metadataErrorsJson[errorKeyName][0]['message']
    elif len(metadataInfosJson) == 1:
        infoKeyName = list(metadataInfosJson.keys())[0]
        message = metadataInfosJson[infoKeyName][0]['message']
    return "responseMessage : " + message

def openLogFile():
    # define the filename of the logfile
    logFileName = timeStamp + "][" + login.environment.get() + "]" + const.batchEditModeDict[editMode] + batchName + ".log"
    # set the full path to the logFile and open it
    if login.environment.get() == "PROD":
        logFileFullPath = r"q:\logFiles\PROD\\" + logFileName
    else:
        logFileFullPath = r"q:\logFiles\\" + logFileName
    return open(logFileFullPath, 'a+')

#######################################################################################################################################

# set the main and second language
if mainLanguage == "ger":
    secondLanguage = "fre"
elif mainLanguage == "fre":
    secondLanguage = "ger"
else:
    writeLog("ERROR - you must either chose \"ger\" or \"fre\" as mainLanguage")
    sys.exit()

# get username, password, environment and check credentials
login = gui.loginWindow()
login.mainloop()
geocatUser = login.username.get()
geocatPassword = login.password.get()
geocatUrlPrefix = login.urlPrefix

logFile = openLogFile()

writeLog("get geocatSession and token")
apiSessionCalls = geocatApiCalls.geocatSession(geocatUrlPrefix, "eng/info?type=me", geocatUser, geocatPassword)
writeLog("TOKEN: " + apiSessionCalls.token)

writeLog("create the list with all uuid-Elements from the searching keyword in geocat")
geocatUuidsList = getGeocatUuids()
writeLog("the list with all uuid-Elements was created and has " + str(len(geocatUuidsList)) + " elements")
logFile.flush()

# iterate aboute all uuids and replace http to attps if it necessary
uuidCounter = 0
for uuid in geocatUuidsList:
    uuidCounter += 1
    # get distribution xml-node
    distributionXmlNode = getDistributionAsRoot(uuid)
    # find all children, which are transferOptions-nodes
    transferOptionsNodesList = distributionXmlNode.findall(".//gmd:transferOptions", ns)
    transferOptionsNodeCounter = 1
    writeLog(str(uuidCounter) + "/" + countOfMDs + ") " + uuid.text)
    # iterate aboute all transferOptions nodes
    for transferOptionsNode in transferOptionsNodesList:
        # find all onLine-nodes in 
        onLineNodesList = transferOptionsNode.findall(".//gmd:onLine", ns)
        onLineNodeCounter = 1
        # iterate aboute all onLine nodes
        for onLineNode in onLineNodesList:
            if onLineNode.find(".//gmd:URL", ns) != None:
                try:
                    httpUrl = onLineNode.find(".//gmd:URL", ns).text
                    if httpUrl != None and httpUrl.startswith(searchString):
                        # insert a "s" after http
                        httpsUrl = httpUrl[:4] + "s" + httpUrl[4:]
                        writeLog(str(uuidCounter) + "/" + countOfMDs + ") " + uuid.text + ": " + httpsUrl)
                        response = replaceUrl(httpsUrl, uuid.text)
                        responseMessage = formatResponse(response)
                        writeLog(responseMessage)
                        logFile.flush()
                except Exception as error:
                    writeLog("on uuid: " + uuid.text + " an exception has occurred: " + str(error))
                    logFile.flush()
                onLineNodeCounter += 1
        transferOptionsNodeCounter += 1
    logFile.flush()
logFile.close()