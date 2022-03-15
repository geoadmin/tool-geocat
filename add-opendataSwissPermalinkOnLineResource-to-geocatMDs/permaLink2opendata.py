# -*-
"""
------------------------------------------------------------------------------------------------------------------------
Autor:      Martin Reithmeier in 2021

Purpose:    add the permalink from opendata.swiss (ods) in geocat MDs. 

Remarks:    

------------------------------------------------------------------------------------------------------------------------
"""

import sys
# sys.path.append("..\\ClassLibrary") # is needed when use outside from Visual Studio
import requests
import urllib3
from pathlib import Path
from requests.auth import HTTPBasicAuth
from geocatFunctionLib import *

mainLanguage = ""
secondLanguage = ""

# desable the exceptions of InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def getGeocatUuidAndOdsIdentifierPair(uuid: str):
    """ returns a dict with the MD uuid and the opendata.swiss (ods) identifier, 
    which is composed of >the uuid from geocat MD< and >@< and >the organisation slug<
    it use the ods-api to find the ods-identifier

    :uuid: the uuid from the geocat MD
    
    :return: dict with uuid and identifier if uuid exist otherwise an empty dict
    """
    odsRequestUrl = const.odsSearchIdentifierUrlPrefix + uuid + "*"
    odsResponse = requests.get(odsRequestUrl, proxies=const.proxyDict, verify=False)
    odsResponseAsText = odsResponse.text
    if uuid in odsResponseAsText:
        odsResponseAsJson = odsResponse.json()
        return {'uuid' : uuid, 'relatedValue' : odsResponseAsJson['result']['results'][0]['identifier']}
    else:
        return {}

def getUuidAndIdentifierPairsList(uuidsList :ElementTree.Element):
    """ create a list of dictionaries containing the MD uuid and the related opendata.swiss identifier

    :uuidsList:

    :return: a list of dictionaries containing the MD uuid and the related opendata.swiss identifier
    """
    uuidAndIdentifierPairsList = []
    countOfMDs = str(len(uuidsList))
    for uuid in uuidsList:
        index = str(uuidsList.index(uuid) + 1)
        writeLog(index + "/" + countOfMDs + ") try to get uuid identifier pair")
        uuidIdentifierPair = getGeocatUuidAndOdsIdentifierPair(uuid.text)
        if uuidIdentifierPair:
            writeLog("    uuid: " + uuidIdentifierPair['uuid'] + ", identifier: " + uuidIdentifierPair['relatedValue'])
            uuidAndIdentifierPairsList.append(uuidIdentifierPair)
        else:
            writeLog("    dataset with uuid: " + uuid.text + " not found on opendata.swiss")
    return uuidAndIdentifierPairsList

def getOnLineNodeParameters(relatedValue :str) -> dict:
    """ set the values for the specific onLine node parameters

    :relatedValue: this is the value that matches the given uuid
    
    :return: the dictionary with the current values
    """
    onLineNodeParameters = {}
    onLineNodeParameters['urlValueDe'] = const.odsLink + "de/perma/" + relatedValue
    onLineNodeParameters['urlValueFr'] = const.odsLink + "fr/perma/" + relatedValue
    onLineNodeParameters['urlValueIt'] = const.odsLink + "it/perma/" + relatedValue
    onLineNodeParameters['urlValueEn'] = const.odsLink + "en/perma/" + relatedValue
    onLineNodeParameters['urlValueRm'] = ""
    onLineNodeParameters['resourceNameValueDe'] = "Permalink opendata.swiss"
    onLineNodeParameters['resourceNameValueFr'] = "Permalink opendata.swiss"
    onLineNodeParameters['resourceNameValueIt'] = "Permalink opendata.swiss"
    onLineNodeParameters['resourceNameValueEn'] = "Permalink opendata.swiss"
    onLineNodeParameters['resourceNameValueRm'] = ""
    onLineNodeParameters['protocol'] = protocol
    return onLineNodeParameters


def updatingRecords(sessionCalls :API.geocatSession, uuidsAndRelatedOdsIdentifiersList):
    """ updating all MDs with the given uuids from the list

    :sessionCalls: current API session-object to send requests by using the GeoNetwork REST API
    :uuidsAndRelatedIdentifiersList: list with dictionaries which have the keywords uuid and relatedValue

    :return: the number of updated MD-records as string
    """
    addCounter = 0
    writeLog("****************************************************************************************************************************")
    writeLog("now, add onLineResources. at first time check if isUpdateToMui and an online resource with the given protocol exist ")
    writeLog("****************************************************************************************************************************")
    countOfMDs = str(len(uuidsAndRelatedOdsIdentifiersList))
    for uuidAndRelatedOdsIdentifier in uuidsAndRelatedOdsIdentifiersList:
        index = str(uuidsAndRelatedOdsIdentifiersList.index(uuidAndRelatedOdsIdentifier) + 1)
        if isUpdateToMui:
            writeLog(index + "/" + countOfMDs + ") check if isUpdateToMui and hasOnlineResource are true, than add xml-Node >onLine<")
        else:
            writeLog(index + "/" + countOfMDs + ") add xml-Node >onLine<")
        if isUpdateToMui and hasOnlineResource(sessionCalls, uuidAndRelatedOdsIdentifier['uuid'], protocol):
            writeLog("     isUpdateToMui and hasOnlineResource are true, now try to delete it")
            deleteOnlineResourceWithGivenProtocol(sessionCalls, protocol, uuid=uuidAndRelatedOdsIdentifier['uuid'])
        onLineNodeParameters = getOnLineNodeParameters(uuidAndRelatedOdsIdentifier['relatedValue'])
        addCounter += addXmlOnLineNode(sessionCalls, uuidAndRelatedOdsIdentifier, onLineNodeParameters)
    return str(addCounter)

def main():
    writeLog("Script: " + batchName + " has started on environment: " + loginData.environment.get())
    global mainLanguage
    global secondLanguage
    mainLanguage, secondLanguage = setMainLanguage("ger")
    sessionCalls = API.geocatSession(loginData.urlPrefix, "eng/info?type=me", loginData.username.get(), loginData.password.get())
    requestCalls = API.geocatRequests(loginData.urlPrefix, loginData.username.get(), loginData.password.get())
    writeLog("****************************************************************************************************************************")
    writeLog("create a list with all uuids from MDs, which have an onLine resource with the protocol >" + protocol + "<")
    writeLog("****************************************************************************************************************************")
    xmlElement = getResponseAsXmlTree(requestCalls, "&protocol=" + protocol, mainLanguage)
    uuidsList = xmlElement.findall(".//uuid")
    if loginData.batchEditMode == "delete":
        deleteOnlineResourceWithGivenProtocol(sessionCalls, protocol, uuidsList=uuidsList, uuid="")
    elif loginData.batchEditMode == "add":
        if not isUpdateToMui:
            usedUuidsList = removeUnusedUuids(requestCalls, uuidsList, keyword, mainLanguage)
        else:
            searchConditionValue = "&keyword=" + keyword + const.isNotHarvested + const.isMetadataType
            usedUuidsList = getResponseAsXmlTree(requestCalls, searchConditionValue, mainLanguage).findall(".//uuid")
        uuidAndIdentifierPairsList = getUuidAndIdentifierPairsList(usedUuidsList)
        isBackup = loginData.isBackup.get()
        if isBackup:
            uuidsBakupList = []
            for uuid in uuidAndIdentifierPairsList:
                uuidsBakupList.append(uuid['uuid'])
            doBackups(sessionCalls, uuidsBakupList, batchName)
        updatedRecords = updatingRecords(sessionCalls, uuidAndIdentifierPairsList)
        writeLog(updatedRecords + " online resources was added (MD records updated)")

try:
    isUpdateToMui = True
    batchName = Path(__file__).stem
    loginData = GUI.loginGUI()
    loginData.mainloop()

    keyword = loginData.keyword.get()
    protocol = loginData.protocol.get()

    logFile = openLogFile(loginData, batchName)
    setLogFile(logFile)
    main()
    logFile.close()
except Exception as error:
    writeLog("Error: " + str(error.args))
