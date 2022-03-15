# -*-
"""
swisstopo geocat function Library
the functions in this module are generalized and can be use in other projects

functions:
    setLogFile(logFile)

    writeLog(logValue: str)
    
    openLogFile(loginData :GUI.loginGUI, batchName :str)
    
    setMainLanguage(language :str)
    
    formatResponse(response :type)
    
    getDistributionNodeAsRoot(sessionCalls :API.geocatSession, uuid :str)
    
    getMdRecordAsXml(sessionCalls :API.geocatSession, uuid :str)
    
    doBackups(sessionCalls :API.geocatSession, uuidsList, batchName :str)
    
    removeEmptyTransferOptionsNode(sessionCalls :API.geocatSession, uuid :str, xpath :str)
    
    getCountOfTransferOptionsNodes(sessionCalls :API.geocatSession, uuid :str)
    
    hasOnlineResource(sessionCalls :API.geocatSession, uuid :str, protocol :str)
    
    getResponseAsXmlTree(requestCalls :API.geocatRequests, searchValue :str, mainLanguage :str)
    
    removeUnusedUuids(requestCalls :API.geocatSession, uuidsList :ElementTree.Element, keyword :str, mainLanguage :str)
    
    getValueAttribute(transferOptionsNumber :int, onLineNodeParameters :dict)
    
    addXmlOnLineBlock(sessionCalls :API.geocatSession, relatedValues :dict, onLineNodeParameters :dict)
    
    getUuidAndRelatedTechLayerPairs(uuidsList :list)
    
    deleteOnlineResourceWithGivenProtocol(sessionCalls :API.geocatSession, protocol :str, **uuids)

    deleteXpath(sessionCalls :API.geocatSession, xPath :str, uuid :str)
"""

import xml.etree.ElementTree as ElementTree
import pandas as pData
import datetime as TimeStamp
import requests
import json
from pathlib import Path

import geocatConstants as const
import geocatLoginGUI as GUI
import geocatApiCalls as API

_logFile = None

def setLogFile(logFile):
    """ it is need to know the reference of the logFile object in this modul

    :logFile: the current logFile object
    """
    global _logFile
    _logFile = logFile

def writeLog(logValue: str):
    """ write logging-informations to file and screen with a timestamp

    :logValue: the string with the data, which you want to log
    """
    logString = TimeStamp.datetime.now().strftime("%Y-%m-%d-%H:%M.%S%f") + ": " + logValue
    print(logString)
    _logFile.write(logString + "\r")
    _logFile.flush()

def openLogFile(loginData :GUI.loginGUI, batchName :str):
    """ set the logfilename and open it 
    the name of logfile consists of timeStamp, environment, batchEditMode and batchName
    the timeStamp ensures thats allways a new logfile is created and the exist one is not overwritten
    the environment says on which server (INT or PROD) the script runed
    the batchEditMode says which mode was used on batch editing
    the batchName is the name of the current script

    :loginData: the current loginGUI object
    :batchName: the name of the current script

    :return: the opened logfile object as TextIOWrapper
    """
    timeStamp = TimeStamp.datetime.now().strftime("%Y-%m-%d-%H%M")
    editMode = loginData.editMode.get()
    # defines the filename of the logfile
    logFileName = timeStamp + "][" + loginData.environment.get() + "]" + const.batchEditModeDict[editMode] + "-" + batchName + ".log"
    # set the full path to the logFile and open it
    if loginData.environment.get() == "PROD":
        logFileFullPath = r"q:\logFiles\PROD\\" + logFileName
    else:
        logFileFullPath = r"q:\logFiles\\" + logFileName
    return  open(logFileFullPath, 'a+')

def setMainLanguage(language :str):
    """ set the main and second language 
    possible values are: ger or fre
    """
    mainLanguage = language
    if mainLanguage == "ger":
        secondLanguage = "fre"
    elif mainLanguage == "fre":
        secondLanguage = "ger"
    else:
        writeLog("ERROR - you must either chose \"ger\" or \"fre\" as mainLanguage")
        sys.exit()
    return mainLanguage, secondLanguage

def formatResponse(response :type) -> str:
    """ this function returns only the most importent information
    :response: the answer of a GeoNetwork REST API request

    :return: only the information, which is important for us
    """
    if response.status_code == 201:
        reason = response.reason
        responseJson = response.json()
        metadataErrorsJson = responseJson['metadataErrors']
        metadataInfosJson = responseJson['metadataInfos']
        if len(metadataErrorsJson) == 1:
            errorKeyName = list(metadataErrorsJson.keys())[0]
            message = "(reason: " + reason + ") Error: " + metadataErrorsJson[errorKeyName][0]['message']
        elif len(metadataInfosJson) == 1:
            infoKeyName = list(metadataInfosJson.keys())[0]
            message = "(reason: " + reason + ") Info: " + metadataInfosJson[infoKeyName][0]['message']
        return "    responseMessage = " + message
    elif response.status_code == 400:
        return response.text

def getDistributionNodeAsRoot(sessionCalls :API.geocatSession, uuid :str) -> ElementTree.Element:
    """ get the xml_Distribution-Node as root from the MD with the given uuid
    :sessionCalls: current API session-object
    :uuid: uuid from the MD-record

    :return: the xml-gmd:MD_Distribution node as ElementTree.Element
    """
    #sessionCalls.setApplicationInHeadersTo("xml")
    #recordUrl = "api/0.1/records/" + uuid
    #respons = sessionCalls.sendGetRequest(recordUrl)
    #sessionCalls.setApplicationInHeadersTo("json")
    xmlElementTree = ElementTree.fromstring(getMdRecordAsXml(sessionCalls, uuid))
    root = xmlElementTree.find(".//gmd:MD_Distribution", const.ns)
    if not root:
        root = xmlElementTree
    return root

def getMdRecordAsXml(sessionCalls :API.geocatSession, uuid :str) -> bytes:
    """ get the MD record as xml from the given uuid
    :sessionCalls: current API session-object
    :uuid: uuid from the MD

    :return: the MD xml in binary format
    """
    sessionCalls.setApplicationInHeadersTo("xml")
    recordUrl = "api/0.1/records/" + uuid
    respons = sessionCalls.sendGetRequest(recordUrl)
    responsContent = respons.content
    sessionCalls.setApplicationInHeadersTo("json")
    return responsContent

def doBackups(sessionCalls :API.geocatSession, uuidsList, batchName :str):
    """ create the backupfolder with the name batchName if it not exist
    write a backup-file in xml-format for all MDs with the given uuids in uuidsList
    :sessionCalls: current API session-object
    :uuidsList: the list with all uuids of the MDs that need a backup
    :batchName: the name of the current script
    """
    uuidBakupsPath = Path(r"Q:\logFiles\Backups\\" + batchName)
    if not uuidBakupsPath.exists():
        uuidBakupsPath.mkdir(parents=True, exist_ok=True)
    countOfMDs = str(len(uuidsList))
    for uuid in uuidsList:
        writeLog(str(uuidsList.index(uuid) + 1) + "/" + countOfMDs + ") write backup from MD " + uuid)
        uuidXmlFilePath = uuidBakupsPath.joinpath(uuid + ".xml")
        mdRecordAsXml = getMdRecordAsXml(sessionCalls, uuid)
        uuidXmlFilePath.write_bytes(mdRecordAsXml)

def removeEmptyTransferOptionsNode(sessionCalls :API.geocatSession, uuid :str, xpath :str) -> int:
    """ remove an empty transferOptions node
    :sessionCalls: current API session-object
    :uuid: uuid from the MD
    :xpath: the path to the Xml-Node

    :return: 1 if the node was deleted, otherwise 0
    """
    value = "<gn_delete></gn_delete>"
    writeLog("      value: " + value)
    writeLog("      xpath: " + xpath)
    urlValue = "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=true"
    writeLog("      urlValue: " + urlValue)
    response = sessionCalls.sendPutRequest(urlValue, value, xpath)
    responseMessage = formatResponse(response)
    writeLog(responseMessage)
    if "Info:" in responseMessage:
        return 1
    else:
        return 0

def getCountOfTransferOptionsNodes(sessionCalls :API.geocatSession, uuid :str) -> str:
    """ get the count of transferoptions-nodes, from the MD with the given uuid
    first, checks if there are empty transferoptions-nodes and remove it from MD

    :sessionCalls: current API session-object
    :uuid: uuid from the MD

    :return: the number of xml-transferoptions nodes, which are not empty
    """
    distribution = getDistributionNodeAsRoot(sessionCalls, uuid)
    if distribution.tag == "{http://www.isotc211.org/2005/gmd}MD_Distribution":
        xmlTransferOptionsNodes = distribution.findall(".//gmd:transferOptions", const.ns)
        writeLog("    check if has empty tronsferOptions nodes and remove it if exist")
        removed = 0
        for transferOptions in reversed(xmlTransferOptionsNodes):
            dto = transferOptions.find("./gmd:MD_DigitalTransferOptions", const.ns)
            if not dto:
                writeLog("      remove empty transferOptionsNode[" + str(xmlTransferOptionsNodes.index(transferOptions) + 1) + "]/" + str(len(xmlTransferOptionsNodes)))
                xpath = ".//gmd:transferOptions[" + str(xmlTransferOptionsNodes.index(transferOptions) + 1) + "]"
                removed += removeEmptyTransferOptionsNode(sessionCalls, uuid, xpath)
        writeLog("      removed " + str(removed) + " empty transferOptionsNodes")
        distribution = None
        xmlTransferOptionsNodes = None
        distribution = getDistributionNodeAsRoot(sessionCalls, uuid)
        xmlTransferOptionsNodes = distribution.findall(".//gmd:transferOptions", const.ns)
        counter = len(xmlTransferOptionsNodes)
        return str(counter)
    else:
        return str(-1)

def hasOnlineResource(sessionCalls :API.geocatSession, uuid :str, protocol :str) -> bool:
    """ check if an online resource with the given protocol exist
    :sessionCalls: current API session-object
    :uuid: uuid from the MD
    :protocol: the protocol name where you search from

    :return: true if exist, otherwise false
    """
    xpath = ".//gmd:onLine//gmd:protocol/gco:CharacterString"
    isExist = False
    distribution = getDistributionNodeAsRoot(sessionCalls, uuid)
    if distribution:
        protocols = distribution.findall(xpath, const.ns)
        for proto in protocols:
            protocolValue = proto.text
            if protocolValue == protocol:
                isExist = True
                break
            else:
                isExist = False
    return isExist

def getResponseAsXmlTree(requestCalls :API.geocatRequests, searchValue :str, mainLanguage :str, start="1", end="1500") -> ElementTree.Element:
    """ get the response of the corresponding search condition as xml tree 

    :requestCalls: object to send requests on the current environment
    :searchValue: the search condition eg. &keyword=keywordValue
    :mainLanguage: the defined main language

    :return: a list with all nodes whitch corresponding the search condition
    """
    writeLog("    get the response of the corresponding search condition: /q?from=" + start + "&to=" + end + searchValue)
    urlValue = mainLanguage + "/q?from=" + start + "&to=" + end + searchValue
    response = requestCalls.sendGetRequest(urlValue)
    countOfMDs = ElementTree.fromstring(response.content).find("./summary").attrib["count"]
    writeLog("    Number of MDs corresponding to your search: " + countOfMDs)
    xmlElementTree = ElementTree.fromstring(response.content)
    return xmlElementTree

def removeUnusedUuids(requestCalls :API.geocatSession, uuidsList :ElementTree.Element, keyword :str, mainLanguage :str):
    """ return a list with all uuids which use to add the opendata.swiss permalink to geocat MDs
    if the keyword uuid not in the protocol uuid then add it to the result list
    :requestCalls: object to send requests on the current environment
    :uuidsList: a list with all MD uuids which have the given protocol

    :return: a list with all MD uuids which haven't the given protocol
    """
    writeLog("****************************************************************************************************************************")
    writeLog("create a list with all uuids from MDs, which have the keyword >" + keyword + "<")
    writeLog("****************************************************************************************************************************")
    searchConditionValue = "&keyword=" + keyword + const.notHarvested + const.isMetadataType #+ const.isValid
    keywordUuidsList =  getResponseAsXmlTree(requestCalls, searchConditionValue, mainLanguage).findall(".//uuid")
    protocolUuidsList = uuidsList
    isEqual = False
    resultList = []
    writeLog("****************************************************************************************************************************")
    writeLog("remove all uuids from keywordList, which have the same uuid in protocolList")
    writeLog("****************************************************************************************************************************")
    for keywordUuid in keywordUuidsList:
        for porotocolUuid in protocolUuidsList:
            if keywordUuid.text == porotocolUuid.text:
                isEqual = True
                break
        if not isEqual:
            resultList.append(keywordUuid)
        else:
            isEqual = False
    writeLog("the list with all needed uuid-Elements was created and has " + str(len(resultList)) + " elements")
    return resultList

def getValueAttribute(transferOptionsNumber :int, onLineNodeParameters :dict):
    """ additional function to addXmlOnLineNode() to build the value-attribute for the batchediting putRequest 

    :transferOptionsNumber: the number of the last transferOptions-node
    :onLineNodeParameters: onLineNode values, which are different for each MD-record

    :return: the joined single line string
    """
    urlValueDe = onLineNodeParameters['urlValueDe']
    urlValueFr = onLineNodeParameters['urlValueFr']
    urlValueIt = onLineNodeParameters['urlValueIt']
    urlValueEn = onLineNodeParameters['urlValueEn']
    urlValueRm = onLineNodeParameters['urlValueRm']
    resourceNameValueDe = onLineNodeParameters['resourceNameValueDe']
    resourceNameValueFr = onLineNodeParameters['resourceNameValueFr']
    resourceNameValueIt = onLineNodeParameters['resourceNameValueIt']
    resourceNameValueEn = onLineNodeParameters['resourceNameValueEn']
    resourceNameValueRm = onLineNodeParameters['resourceNameValueRm']
    protocol = onLineNodeParameters['protocol']
    batchEditModeTag = "<gn_add>"
    batchEditModeCloseTag = "</gn_add>"
    if transferOptionsNumber > 0:
        resourceTypeTag = "<gmd:onLine " + const.namespaces + ">"
    else:
        resourceTypeTag = "<gmd:onLine>"
    resourceTypeCloseTag = "</gmd:onLine>"
    protocolBlock = "<gmd:protocol><gco:CharacterString>" + protocol + "</gco:CharacterString></gmd:protocol>"
    defaultResourceName = "<gco:CharacterString>" + resourceNameValueDe + "</gco:CharacterString>"
    resourceNameDe = "<gmd:textGroup><gmd:LocalisedCharacterString locale=\"#DE\">" + resourceNameValueDe + "</gmd:LocalisedCharacterString></gmd:textGroup>"
    resourceNameFr = "<gmd:textGroup><gmd:LocalisedCharacterString locale=\"#FR\">" + resourceNameValueFr + "</gmd:LocalisedCharacterString></gmd:textGroup>"
    resourceNameIt = "<gmd:textGroup><gmd:LocalisedCharacterString locale=\"#IT\">" + resourceNameValueIt + "</gmd:LocalisedCharacterString></gmd:textGroup>"
    resourceNameEn = "<gmd:textGroup><gmd:LocalisedCharacterString locale=\"#EN\">" + resourceNameValueEn + "</gmd:LocalisedCharacterString></gmd:textGroup>"
    if resourceNameValueRm:
        resourceNameRm = "<gmd:textGroup><gmd:LocalisedCharacterString locale=\"#RM\">" + resourceNameValueRm + "</gmd:LocalisedCharacterString></gmd:textGroup>"
    else:
        resourceNameRm = ""
    localisedResourceNameBlock = "<gmd:PT_FreeText>" + resourceNameDe + resourceNameFr + resourceNameIt + resourceNameEn + resourceNameRm + "</gmd:PT_FreeText>"
    resourceNameBlock = "<gmd:name xsi:type=\"gmd:PT_FreeText_PropertyType\">" + defaultResourceName + localisedResourceNameBlock + "</gmd:name>"
    resourceDescriptionBlock = "<gmd:description xsi:type=\"gmd:PT_FreeText_PropertyType\">" + defaultResourceName + localisedResourceNameBlock + "</gmd:description>"
    defaultUrlBlock = "<gmd:URL>" + urlValueDe + "</gmd:URL>"
    localisedUrlDe = "<che:URLGroup><che:LocalisedURL locale=\"#DE\">" + urlValueDe + "</che:LocalisedURL></che:URLGroup>"
    localisedUrlFr = "<che:URLGroup><che:LocalisedURL locale=\"#FR\">" + urlValueFr + "</che:LocalisedURL></che:URLGroup>"
    localisedUrlIt = "<che:URLGroup><che:LocalisedURL locale=\"#IT\">" + urlValueIt + "</che:LocalisedURL></che:URLGroup>"
    localisedUrlEn = "<che:URLGroup><che:LocalisedURL locale=\"#EN\">" + urlValueEn + "</che:LocalisedURL></che:URLGroup>"
    if urlValueRm:
        localisedUrlRm = "<che:URLGroup><che:LocalisedURL locale=\"#RM\">" + urlValueRm + "</che:LocalisedURL></che:URLGroup>"
    else:
        localisedUrlRm = ""
    localisedUrlBlock = "<che:PT_FreeURL>" + localisedUrlDe + localisedUrlFr + localisedUrlIt + localisedUrlEn + localisedUrlRm + "</che:PT_FreeURL>"
    linkageBlock = "<gmd:linkage xsi:type=\"che:PT_FreeURL_PropertyType\">" + defaultUrlBlock + localisedUrlBlock + "</gmd:linkage>"
    onlineResourceBlock = "<gmd:CI_OnlineResource>" + linkageBlock + protocolBlock + resourceNameBlock + resourceDescriptionBlock + "</gmd:CI_OnlineResource>"
    buildedResourceType = resourceTypeTag + onlineResourceBlock + resourceTypeCloseTag
    if transferOptionsNumber > 0:
        return batchEditModeTag + buildedResourceType + batchEditModeCloseTag
    else:
        return batchEditModeTag + "<gmd:MD_DigitalTransferOptions " + const.namespaces + ">" + buildedResourceType + "</gmd:MD_DigitalTransferOptions>" +  batchEditModeCloseTag

def addXmlOnLineNode(sessionCalls :API.geocatSession, relatedValues :dict, onLineNodeParameters :dict):
    """ main function to add <gmd:onLine> ... </gmd:onLine> 

    :sessionCalls: current API session-object
    :relatedValues: {"uuid" : "value", "relatedValue" : "value"} data pair: uuid with the related value 
    :onLineNodeParameters: onLineNode values, which are different for each MD-record 

    :return:
    """
    transferOptionsNodeCount = getCountOfTransferOptionsNodes(sessionCalls, relatedValues['uuid'])
    # need if <gmd:distributionInfo> node not exist
    if int(transferOptionsNodeCount) == -1:
        value = "<gn_add><gmd:distributionFormat " + const.namespaces + " xlink:href='local://srv/api/registries/entries/388d711d-c1ea-49ea-a02d-5868b1174b55?lang=ger,fre,eng,ita&amp;schema=iso19139.che'><gmd:MD_Format><gmd:name><gco:CharacterString>autres formats sur demande / andere Formate auf Anfrage</gco:CharacterString></gmd:name><gmd:version gco:nilReason='missing'><gco:CharacterString/></gmd:version></gmd:MD_Format></gmd:distributionFormat></gn_add>"
        xpath = "/che:CHE_MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution"
        urlValue = "api/0.1/records/batchediting?uuids=" + relatedValues['uuid'] + "&updateDateStamp=true"
        writeLog("    MD has no online resource, its need to add additional data")
        writeLog("      urlValue: " + urlValue)
        writeLog("      value: " + value)
        writeLog("      xpath: " + xpath)
        response = sessionCalls.sendPutRequest(urlValue, value, xpath)
        responseMessage = formatResponse(response)
        writeLog(responseMessage)
        value = "<gn_add><gmd:transferOptions " + const.namespaces + " ></gmd:transferOptions></gn_add>"
        response = sessionCalls.sendPutRequest(urlValue, value, xpath)
        transferOptionsNodeCount = "0"
    value = getValueAttribute(int(transferOptionsNodeCount), onLineNodeParameters)
    if int(transferOptionsNodeCount) > 0:
        xpath = "/che:CHE_MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions[" + transferOptionsNodeCount + "]/gmd:MD_DigitalTransferOptions"
    elif int(transferOptionsNodeCount) == 0:
        xpath = "/che:CHE_MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions"
    urlValue = "api/0.1/records/batchediting?uuids=" + relatedValues['uuid'] + "&updateDateStamp=true"
    writeLog("    urlValue: " + urlValue)
    writeLog("    value: " + value)
    writeLog("    xpath: " + xpath)
    response = sessionCalls.sendPutRequest(urlValue, value, xpath)
    responseMessage = formatResponse(response)
    writeLog(responseMessage)
    if "Info:" in responseMessage:
        return 1
    else:
        return 0

def getUuidAndRelatedTechLayerPairs(uuidsList :list, dataSource :str, inputFilename=""):
    """ return the list with all needed uuid and it's related techLayer pairs 

    :requestCalls:
    :uuidsList: list with all possible uuids
    :dataSource:

    :return: list[dict{uuid:uuid, relatedValue:techlayer}]

    responseData[12]['IDGEOCAT']
    responseData[12]['LAYERBODID']
    """
    resultList = []
    idGeoCat = 'idGeoCat'
    layerBodId = 'layerBodId'
    bodExportFilePath = inputFilename
    bodExportFileAsList = []
    if dataSource == "API3":
        url = const.api3RequestUrl
        response = requests.get(url, proxies=const.proxyDict, verify=False)
        responseLayers = response.json()['layers']
    elif dataSource == "BMD":
        url = const.bmdRequestUrl
        idGeoCat = idGeoCat.upper()
        layerBodId = layerBodId.upper()
        #response = requestCalls.sendGetRequest(url)
        response = requests.get(url)
        responseLayers = response.json()
    elif dataSource == "BOD":
        with open(bodExportFilePath) as bodFp:
            for line in bodFp:
                bodExportFileAsList.append(line.rstrip("\n"))
        bodFp.close()
        for uuidTechLayer in bodExportFileAsList:
            resultLine = {}
            geocat_id, dataset_id = uuidTechLayer.split(";")
            if len(geocat_id) == 36:
                resultLine['uuid'] = geocat_id
                resultLine['relatedValue'] = dataset_id
                resultList.append(resultLine)
        return resultList

    for uuid in uuidsList:
        countOfMDs = str(len(uuidsList))
        writeLog(str(uuidsList.index(uuid) + 1) + "/" + countOfMDs + ") search related techLayer from uuid: " + uuid.text)
        for layer in responseLayers:
            if uuid.text == layer[idGeoCat]:
                resultLine = {}
                resultLine['uuid'] = layer[idGeoCat]
                resultLine['relatedValue'] = layer[layerBodId]
                resultList.append(resultLine)
    writeLog("the list with all uuid-techLayer pairs was created and has " + str(len(resultList)) + " dictionaries")
    return resultList

def deleteOnlineResourceWithGivenProtocol(sessionCalls :API.geocatSession, protocol :str, **uuids):
    """ remove one or all online resource, which having the given protocol eg. ESRI:REST

    :sessionCalls: current API session-object
    :protocol: the name of the protocol
    :**uuids:
    :uuids['uuid']: only one uuid, use if only one MD record to remove the online resource
    :uuids['uuidsList']: list of uuids, use if more than one MD record to remove the online resource
    """
    value = "<gn_delete></gn_delete>"
    xpath = ".//gmd:onLine[*/gmd:protocol/*/text() = '" + protocol + "']"
    writeLog("      value: " + value)
    writeLog("      xpath: " + xpath)
    def runTask(uuid :str):
        """ nested function to do the same things of both conditions"""
        urlValue = "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=true"
        writeLog("      urlValue: " + urlValue)
        response = sessionCalls.sendPutRequest(urlValue, value, xpath)
        responseMessage = formatResponse(response)
        writeLog(responseMessage)
        if "Info:" in responseMessage:
            return 1
        else:
            return 0

    deleteCounter = 0
    if uuids['uuid']:
        deleteCounter += runTask(uuids['uuid'])
    else:
        uuidsList = uuids['uuidsList']
        for uuid in uuidsList:
            countOfMDs = str(len(uuidsList))
            writeLog(str(uuidsList.index(uuid) + 1) + "/" + countOfMDs + ") delete xml-Node onLine")
            deleteCounter += runTask(uuid.text)
    writeLog("      " + str(deleteCounter) + " online resources was deleted")

def deleteXpath(sessionCalls :API.geocatSession, xPath :str, uuid :str):
    value = "<gn_delete></gn_delete>"
    xpath = xPath
    writeLog("      value: " + value)
    writeLog("      xpath: " + xpath)
    urlValue = "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=true"
    writeLog("      urlValue: " + urlValue)
    response = sessionCalls.sendPutRequest(urlValue, value, xpath)
    responseMessage = formatResponse(response)
    writeLog(responseMessage)
