# -*-
'''
------------------------------------------------------------------------------------------------------------------------
Autor:      Reithmeier Martin (rem) in 2021 

Purpose:    This script add one onLine resource with the "RestFul-API geo.admin.ch-Link 
            as service to the record with the given uuid"

Remarks:    
------------------------------------------------------------------------------------------------------------------------
'''

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

def removeOnLineResourceWithGeneralLink(sessionCalls :API.geocatSession, uuidsList :ElementTree.Element) -> int:
    """ delete the onLine Resource whitch have a service link like https://api3.geo.admin.ch
    :sessionCalls:
    :uuid: the MD uuid

    :return: the count of removed onLine Resource 
    """
    def isOnLineResourceHasGeneralLink(uuid :str) -> bool:
        """ this function check, if the current MD with the given uuid has an url with general information 
        :sessionCalls:
        :uuid: the MD uuid

        :return: True if exist otherwise False 
        """
        distributionXmlNode = getDistributionNodeAsRoot(sessionCalls, uuid)
        allDefaultUrls = distributionXmlNode.findall(".//gmd:onLine//gmd:URL", const.ns)
        isExist = False
        for url in allDefaultUrls:
            urlValue = url.text
            if urlValue == "https://api3.geo.admin.ch":
                isExist = True
                break
            else:
                isExist = False
        return isExist

    writeLog("****************************************************************************************************************************")
    writeLog("remove all uuids from MDs, which have an onLine resource with the service-link like >https://api3.geo.admin.ch<")
    writeLog("****************************************************************************************************************************")
    removeCounter = 0
    for uuid in uuidsList:
        countOfMDs = str(len(uuidsList))
        writeLog(str(uuidsList.index(uuid) + 1) + "/" + countOfMDs + ") check onLineResource has a generalLink on MD uuid: " + uuid.text)
        if isOnLineResourceHasGeneralLink(uuid.text):
            deleteOnlineResourceWithGivenProtocol(sessionCalls, protocol, uuid=uuid.text)
            removeCounter += 1
    return removeCounter

def getOnLineNodeParameters(relatedValue :str):
    onLineNodeParameters = {}
    onLineNodeParameters['urlValueDe'] = const.restFulApiUrlPrefix + relatedValue
    onLineNodeParameters['urlValueFr'] = const.restFulApiUrlPrefix + relatedValue
    onLineNodeParameters['urlValueIt'] = const.restFulApiUrlPrefix + relatedValue
    onLineNodeParameters['urlValueEn'] = const.restFulApiUrlPrefix + relatedValue
    onLineNodeParameters['urlValueRm'] = const.restFulApiUrlPrefix + relatedValue
    onLineNodeParameters['resourceNameValueDe'] = "RESTful API von geo.admin.ch"
    onLineNodeParameters['resourceNameValueFr'] = "RESTful API de geo.admin.ch"
    onLineNodeParameters['resourceNameValueIt'] = "RESTful API da geo.admin.ch"
    onLineNodeParameters['resourceNameValueEn'] = "RESTful API from geo.admin.ch"
    onLineNodeParameters['resourceNameValueRm'] = "RESTful API dad geo.admin.ch"
    onLineNodeParameters['protocol'] = protocol
    return onLineNodeParameters

def updatingRecords(sessionCalls :API.geocatSession, uuidAndTechLayerPairsList):
    """ updating all MDs with the given uuids from the list
    :sessionCalls: object to send requests by using the GeoNetwork REST API
    :uuidsIdentifiersList:

    :return: the number of updated MD records as string
    """
    def isNotBadRequest(uuidTechLayerPair :dict) -> bool:
        """ check if the service-url gives not a bad request
        :uuidTechLayerPair: dictionary with the values of uuid and relatedValue (techLayer)

        :return: True if status_code = 200 otherwise False
        """
        url = const.restFulApiUrlPrefix + uuidTechLayerPair['relatedValue']
        response = requests.get(url, proxies=const.proxyDict, verify=False)
        if response.status_code == 200:
            return True
        else:
            text = response.text
            lines = text.splitlines()
            outText = ""
            for line in lines:
                if line:
                    outText += line + ": "
            writeLog("    " + outText + "\n                               no online resource added in MD " + uuidTechLayerPair['uuid'])
            return False

    addCounter = 0
    writeLog("****************************************************************************************************************************")
    writeLog("now, add onLineResources if isNotBadRequest")
    writeLog("****************************************************************************************************************************")
    countOfMDs = str(len(uuidAndTechLayerPairsList))
    for uuidAndTechlayerPair in uuidAndTechLayerPairsList:
        writeLog(str(uuidAndTechLayerPairsList.index(uuidAndTechlayerPair) + 1) + "/" + countOfMDs + ") add xml-Node >onLine<")
        if isNotBadRequest(uuidAndTechlayerPair):
            onLineNodeParameters = getOnLineNodeParameters(uuidAndTechlayerPair['relatedValue'])
            addCounter += addXmlOnLineNode(sessionCalls, uuidAndTechlayerPair, onLineNodeParameters)
    return str(addCounter)

def main():
    """ logical main sequence """
    writeLog("Script: " + batchName + " has started on environment: " + loginData.environment.get())
    global mainLanguage
    global secondLanguage
    mainLanguage, secondLanguage = setMainLanguage("ger")
    sessionCalls = API.geocatSession(loginData.urlPrefix, "eng/info?type=me", loginData.username.get(), loginData.password.get())
    requestCalls = API.geocatRequests(loginData.urlPrefix, loginData.username.get(), loginData.password.get())
    writeLog("****************************************************************************************************************************")
    writeLog("create a list with all uuids from MDs, which have an onLine resource with the protocol >" + protocol + "<")
    writeLog("****************************************************************************************************************************")
    geocatUuidsList = getResponseAsXmlTree(requestCalls, "&protocol=" + protocol, mainLanguage).findall(".//uuid")
    if loginData.batchEditMode == "delete":
        deleteOnlineResourceWithGivenProtocol(sessionCalls, protocol, uuidsList=geocatUuidsList, uuid="")
    elif loginData.batchEditMode == "add":
        if isNeedToRemoveOlrWithGeneralLinks:
            removedOnlineResources = removeOnLineResourceWithGeneralLink(sessionCalls, geocatUuidsList)
            writeLog("Removed onLine resources: " + str(removedOnlineResources))
            geocatUuidsList.clear()
            writeLog("****************************************************************************************************************************")
            writeLog("again: create a list with all uuids from MDs, which have an onLine resource with the protocol >" + protocol + "< (!! BFE !!)")
            writeLog("****************************************************************************************************************************")
            geocatUuidsList = getResponseAsXmlTree(requestCalls, "&protocol=" + protocol, mainLanguage).findall(".//uuid")
        usedUuidsList = removeUnusedUuids(requestCalls, geocatUuidsList, keyword, mainLanguage)
        uuidAndTechLayerPairsList = getUuidAndRelatedTechLayerPairs(usedUuidsList, loginData.dataSource.get())
        isBackup = loginData.isBackup.get()
        if isBackup:
            uuidsBakupList = []
            for uuid in uuidAndTechLayerPairsList:
                uuidsBakupList.append(uuid['uuid'])
            doBackups(sessionCalls, uuidsBakupList, batchName)
        updatedRecords = updatingRecords(sessionCalls, uuidAndTechLayerPairsList)
        writeLog("****************************************************************************************************************************")
        writeLog("---finish---  total " + updatedRecords + " online resources was added")
        writeLog("****************************************************************************************************************************")
    logFile.close()

try:
    isNeedToRemoveOlrWithGeneralLinks = False
    batchName = Path(__file__).stem
    loginData = GUI.loginGUI()
    loginData.mainloop()        # open the login window

    keyword = loginData.keyword.get()
    protocol = loginData.protocol.get()

    logFile = openLogFile(loginData, batchName)     # open the logFile
    setLogFile(logFile)         # make logFile visible in geocatFunctionLib
    main()                      # call the function main
    logFile.close()
except Exception as error:
    writeLog("Error: " + str(error.args))   
