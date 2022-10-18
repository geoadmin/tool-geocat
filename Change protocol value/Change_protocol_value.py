# -*-
import sys
# sys.path.append("..\\ClassLibrary") # is needed when use outside from Visual Studio
import urllib3
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from requests.auth import HTTPBasicAuth
import geocatLoginGUI as GUI
import geocatGroups as groupOwners
import geocatLoginGUI as GUI
import geocatApiCalls as API
import geocatConstants as const
import geocatFunctionLib as funcLib

# desable the exceptions of InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ChangeProtocolValue:
    '''
    Autor:      Reithmeier Martin (rem) in 2022

    Purpose:    

    Remarks:    
    jira-Tickets: https://jira.swisstopo.ch/browse/METADATA_SB-218 and https://jira.swisstopo.ch/browse/METADATA_SB-244

    '''
    # Attributes
    __funcLib = funcLib.FunctionLibrary()
    __loginData = GUI.LoginGUI()
    __batchName = Path(__file__).stem
    __sessionCalls = None
    __requestCalls = None

    def __init__(self):
        self.__mainLanguage = ""
        self.__secondLanguage = ""
        self.__mainLanguage, self.__secondLanguage = self.__funcLib.setMainLanguage("ger")
        self.__loginData.mainloop()        # open the login window
        self.__logFile = self.__funcLib.openLogFile(self.__loginData, self.__batchName)     # open the logFile
        self.__funcLib.setLogFile(self.__logFile)         # make logFile visible in geocatFunctionLib

    def closeLogFile(self):
        self.__logFile.close()

    def writeLog(self, logValue :str):
        self.__funcLib.writeLog(logValue)

    def __searchUuids(self):
        """ search all needed uuids """
        _searchValue = const.searchFilter + const.groupOwner + str(self.__loginData.groupId.get())
        _xmlDataAsElement = self.__funcLib.getResponseAsXmlTree(_searchValue, self.__mainLanguage)
        _uuidsAsElementList = _xmlDataAsElement.findall(".//uuid")
        _uuidsList = []
        for uuid in _uuidsAsElementList:
            _uuidsList.append(uuid.text)
        return _uuidsList

    def __changeProtocolValue(self, uuidsList :list):
        _countOfMDs = str(len(uuidsList))
        _uuidCounter = 0
        for uuid in uuidsList:
            _uuidCounter += 1
            # get distribution xml-node
            _distributionXmlNode = self.__funcLib.getDistributionNodeAsRoot(uuid)
            # find all children, which are transferOptions-nodes
            _transferOptionsNodesList = _distributionXmlNode.findall(".//gmd:transferOptions", const.ns)
            _transferOptionsNodeCounter = 1
            self.__funcLib.writeLog(str(_uuidCounter) + "/" + _countOfMDs + ") " + uuid)
            # iterate aboute all transferOptions nodes
            for transferOptionsNode in _transferOptionsNodesList:
                # find all onLine-nodes in 
                _onLineNodesList = transferOptionsNode.findall(".//gmd:onLine", const.ns)
                _onLineNodeCounter = 1
                # iterate aboute all onLine nodes
                for onLineNode in _onLineNodesList:
                    if onLineNode.find(".//gmd:protocol", const.ns) != None:
                        if onLineNode.find(".//gmd:linkage/gmd:URL", const.ns) != None:
                            _urlValue = onLineNode.find(".//gmd:linkage/gmd:URL", const.ns).text
                            if _urlValue.startswith("http") or _urlValue.startswith("https"):
                                _urlList = _urlValue.split('//')
                                _urlAddress = _urlList[1].rstrip('/')
                                if _urlAddress in const.valuesToChange:
                                    _oldProtocolValue = onLineNode.find(".//gmd:protocol/gco:CharacterString", const.ns).text
                                    _newProtocolValue = const.valuesToChange[_urlAddress]
                                    if _oldProtocolValue != _newProtocolValue:
                                        _value = "<gn_replace><gco:CharacterString " + const.namespaces + ">" + _newProtocolValue + "</gco:CharacterString></gn_replace>"
                                        _xpath = ".//gmd:transferOptions[" + str(_transferOptionsNodeCounter) + "]//gmd:onLine[" + str(_onLineNodeCounter) + "]//gmd:protocol"
                                        self.__funcLib.writeLog("    value: " + _value)
                                        self.__funcLib.writeLog("    xpath: " + _xpath)
                                        _urlValue  = "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=true"
                                        _response = self.__sessionCalls.sendPutRequest(_urlValue, _value, _xpath)
                                        self.__funcLib.writeLog(self.__funcLib.formatResponse(_response))
                    _onLineNodeCounter += 1
                _transferOptionsNodeCounter += 1

    def main(self):
        """
        Purpose:
        """
        self.__funcLib.writeLog("Script: " + self.__batchName + " has started on environment: " + self.__loginData.environment.get())
        self.__sessionCalls = API.GeocatSession(self.__loginData.urlPrefix, "eng/info?type=me", self.__loginData.username.get(), self.__loginData.password.get())
        self.__requestCalls = API.GeocatRequests(self.__loginData.urlPrefix, self.__loginData.username.get(), self.__loginData.password.get())
        self.__funcLib.setApiCalls(self.__sessionCalls, self.__requestCalls)
        _uuidsList = self.__searchUuids()
        # todo dispatcher
        if self.__loginData.backupMode.get() == "Restore":
            self.__funcLib.doRestor(self.__batchName)
        _isBackup = self.__loginData.isBackup.get()
        if _isBackup:
            _uuidsBakupList = _uuidsList
            self.__funcLib.doBackups(_uuidsBakupList, self.__batchName)
        if self.__loginData.batchEditMode == "add":
            pass
        elif self.__loginData.batchEditMode == "replace":
            uuidsList = self.__searchUuids()
            self.__changeProtocolValue(uuidsList)

try:
    changeProtocolValue = ChangeProtocolValue()     # create the renameProtocolValue-object
    changeProtocolValue.main()                      # call the main-function 
    changeProtocolValue.closeLogFile()
except Exception as error:
    changeProtocolValue.writeLog("Error: " + str(error.args))