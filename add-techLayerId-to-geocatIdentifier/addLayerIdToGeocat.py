# -*-
'''
------------------------------------------------------------------------------------------------------------------------
Autor:      Reithmeier Martin (rem) in 2022

Purpose:    /che:CHE_MD_Metadata/gmd:identificationInfo/che:CHE_MD_DataIdentification/gmd:citation/gmd:CI_Citation 
            add this path /gmd:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString

Remarks:    
			</gmd:date> :after
			<gmd:identifier>
				<gmd:MD_Identifier>
					<gmd:code>
						<gco:CharacterString>ch.swisstopo.lubis-luftbilder_farbe</gco:CharacterString>
					</gmd:code>
				</gmd:MD_Identifier>
			</gmd:identifier> :before
			<gmd:collectiveTitle xsi:type="gmd:PT_FreeText_PropertyType">

------------------------------------------------------------------------------------------------------------------------
'''

import sys
# sys.path.append("..\\ClassLibrary") # is needed when use outside from Visual Studio
import urllib3
from pathlib import Path
from requests.auth import HTTPBasicAuth
from geocatFunctionLib import *

mainLanguage = ""
secondLanguage = ""

# desable the exceptions of InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def getCitationNodeAsRoot(sessionCalls :API.geocatSession, uuid :str) -> ElementTree.Element:
    """ get the xml_Citation-Node as root from the MD with the given uuid

    :sessionCalls: current API session-object
    :uuid: uuid from the MD

    :return: the xml-gmd:CI_Citation-node as root
    """
    sessionCalls.setApplicationInHeadersTo("xml")
    recordUrl = "api/0.1/records/" + uuid
    respons = sessionCalls.sendGetRequest(recordUrl)
    sessionCalls.setApplicationInHeadersTo("json")
    return ElementTree.fromstring(respons.content).find(".//gmd:CI_Citation", const.ns)

def isTechLayerNameExist(sessionCalls :API.geocatSession, uuid :str) -> bool:
    """ 
    :sessionCalls: current API session-object
    :uuid: uuid from the MD
    """
    citationXpath = getCitationNodeAsRoot(sessionCalls, uuid)
    identifierXpath = citationXpath.findall(".//gmd:MD_Identifier", const.ns)
    if identifierXpath:
        return True
    else:
        return False

def getUsedUuidsList(sessionCalls :API.geocatSession, uuidsList :ElementTree.Element):
    """ 
    :sessionCalls: current API session-object
    :uuidsList: uuids from the MDs
    """
    countOfMDs = str(len(uuidsList))
    resultList = []
    for uuid in uuidsList:
        writeLog(str(uuidsList.index(uuid) + 1) + "/" + countOfMDs + ") check if techLayerName exist on MD " + uuid)
        if not isTechLayerNameExist(sessionCalls, uuid.text):
            resultList.append(uuid)
    return resultList

def addXmlIdentifierNode(sessionCalls :API.geocatSession, uuidTechlayerPair :dict):
    """ """
    def getValueAttribute(techLayer :str):
        """ build the value-attribute for the batchediting putRequest 
        """
        batchEditModeTag = "<gn_add>"
        batchEditModeCloseTag = "</gn_add>"
        identifierCodeTag = "<gmd:identifier " + const.namespaces + "><gmd:MD_Identifier><gmd:code>"
        identifierCodeCloseTag = "</gmd:code></gmd:MD_Identifier></gmd:identifier>"
        layerName = "<gco:CharacterString>" + techLayer + "</gco:CharacterString>"

        return batchEditModeTag + identifierCodeTag + layerName + identifierCodeCloseTag + batchEditModeCloseTag

    value = getValueAttribute(uuidTechlayerPair['relatedValue'])
    # get the count of the transferoptions tag
    xpath = "/che:CHE_MD_Metadata/gmd:identificationInfo/che:CHE_MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier[1]"
    urlValue = "api/0.1/records/batchediting?uuids=" + uuidTechlayerPair['uuid'] + "&updateDateStamp=true"
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

def main():
    writeLog("Script: " + batchName + " has started on environment: " + loginData.environment.get())
    global mainLanguage
    global secondLanguage
    mainLanguage, secondLanguage = setMainLanguage("ger")
    sessionCalls = API.geocatSession(loginData.urlPrefix, "eng/info?type=me", loginData.username.get(), loginData.password.get())
    requestCalls = API.geocatRequests(loginData.urlPrefix, loginData.username.get(), loginData.password.get())
    #uuidsList = getResponseAsXmlTree(requestCalls, "&keyword=" + keyword, mainLanguage).findall(".//uuid")
    #usedUuidsList = getUsedUuidsList(sessionCalls, uuidsList)
    uuidAndTechLayerPairsList = getUuidAndRelatedTechLayerPairs(None, dataSource)
    isBackup = loginData.isBackup.get()
    if isBackup:
        uuidsBakupList = []
        for uuidTechLayer in uuidAndTechLayerPairsList:
            uuidsBakupList.append(uuidTechLayer['uuid'])
        doBackups(sessionCalls, uuidsBakupList, batchName)
    if loginData.batchEditMode == "add":
        addCounter = 0
        countOfMDs = str(len(uuidAndTechLayerPairsList))
        for uuidAndTechlayerPair in uuidAndTechLayerPairsList:
            if not isTechLayerNameExist(sessionCalls, uuidAndTechlayerPair['uuid']):
                writeLog(str(uuidAndTechLayerPairsList.index(uuidAndTechlayerPair) + 1) + "/" + countOfMDs + ") add identifier xml-Node in MD: " + uuidAndTechlayerPair['uuid'])
                addCounter += addXmlIdentifierNode(sessionCalls, uuidAndTechlayerPair)
            else:
                writeLog(str(uuidAndTechLayerPairsList.index(uuidAndTechlayerPair) + 1) + "/" + countOfMDs + ") identifier xml-Node already exist in MD: " + uuidAndTechlayerPair['uuid'])
        writeLog(str(addCounter) + " identifiers was added")
    elif loginData.batchEditMode == "delete":
        countOfMDs = str(len(uuidAndTechLayerPairsList))
        for uuidAndTechlayerPair in uuidAndTechLayerPairsList:
            if isTechLayerNameExist(sessionCalls, uuidAndTechlayerPair['uuid']):
                writeLog(str(uuidAndTechLayerPairsList.index(uuidAndTechlayerPair) + 1) + "/" + countOfMDs + ") delete identifier xml-Node in MD: " + uuidAndTechlayerPair['uuid'])
                deleteXpath(sessionCalls, ".//gmd:identifier", uuidAndTechlayerPair['uuid'])

try:
    batchName = Path(__file__).stem
    loginData = GUI.loginGUI()
    loginData.mainloop()        # open the login window

    keyword = loginData.keyword.get()
    protocol = loginData.protocol.get()
    dataSource = loginData.dataSource.get()

    logFile = openLogFile(loginData, batchName)     # open the logFile
    setLogFile(logFile)         # make logFile visible in geocatFunctionLib
    main()                      # call the function main
    logFile.close()
except Exception as error:
    writeLog("Error: " + str(error.args))   
