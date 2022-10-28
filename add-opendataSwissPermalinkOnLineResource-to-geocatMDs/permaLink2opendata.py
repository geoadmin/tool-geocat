
import sys
# sys.path.append("..\\ClassLibrary") # is needed when use outside from Visual Studio
import requests
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

class PermaLink2opendata():
    """
    Autor:      Martin Reithmeier in 2021

    Purpose:    add the permalink from opendata.swiss (ods) in geocat MDs, which has the keyword opendata.swiss

    Remarks:    

    """

    # Attributes
    __funcLib = funcLib.FunctionLibrary()
    __loginData = GUI.LoginGUI()
    __batchName = Path(__file__).stem
    __sessionCalls = None
    __requestCalls = None
    __isUpdateToMui = False

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

    def __getGeocatUuidAndOdsIdentifierPair(self, uuid: str):
        """ returns a dict with the MD uuid and the opendata.swiss (ods) identifier, 
        which is composed of >the uuid from geocat MD< and >@< and >the organisation slug<
        it use the ods-api to find the ods-identifier
    
        uuid: the uuid from the geocat MD
        
        return: dict with uuid and identifier if uuid exist otherwise an empty dict
        """
        _odsRequestUrl = const.odsSearchIdentifierUrlPrefix + uuid + "*"
        _odsResponse = requests.get(_odsRequestUrl, proxies=const.proxyDict, verify=False)
        _odsResponseText = _odsResponse.text
        if uuid in _odsResponseText:
            _odsResponseAsJson = _odsResponse.json()
            return {'uuid' : uuid, 'relatedValue' : _odsResponseAsJson['result']['results'][0]['identifier']}
        else:
            return {}
    
    def __getUuidAndIdentifierPairsList(self, uuidsList :ElementTree.Element):
        """ create a list of dictionaries containing the MD-uuid and the related opendata.swiss identifier
    
        uuidsList (list[ElementTree.Element]):
    
        return: a list of dictionaries containing the MD uuid and the related opendata.swiss identifier
        """
        _uuidAndIdentifierPairsList = []
        _countOfMDs = str(len(uuidsList))
        for uuid in uuidsList:
            _index = str(uuidsList.index(uuid) + 1)
            self.writeLog(_index + "/" + _countOfMDs + ") try to get uuid identifier pair")
            _uuidIdentifierPair = self.__getGeocatUuidAndOdsIdentifierPair(uuid.text)
            if _uuidIdentifierPair:
                self.writeLog("    uuid: " + _uuidIdentifierPair.get('uuid') + ", identifier: " + _uuidIdentifierPair.get('relatedValue'))
                _uuidAndIdentifierPairsList.append(_uuidIdentifierPair)
            else:
                self.writeLog("    dataset with uuid: " + uuid.text + " not found on opendata.swiss")
        return _uuidAndIdentifierPairsList
    
    def __getOnLineNodeParameters(self, relatedValue :str):
        """ set the values for the specific onLine node parameters
    
        relatedValue: this is the value that matches the given uuid
        
        return: the dictionary with the current values
        """
        _onLineNodeParameters = {}
        _onLineNodeParameters['urlValueDe'] = const.odsLink + "de/perma/" + relatedValue
        _onLineNodeParameters['urlValueFr'] = const.odsLink + "fr/perma/" + relatedValue
        _onLineNodeParameters['urlValueIt'] = const.odsLink + "it/perma/" + relatedValue
        _onLineNodeParameters['urlValueEn'] = const.odsLink + "en/perma/" + relatedValue
        _onLineNodeParameters['urlValueRm'] = ""
        _onLineNodeParameters['resourceNameValueDe'] = "Permalink opendata.swiss"
        _onLineNodeParameters['resourceNameValueFr'] = "Permalink opendata.swiss"
        _onLineNodeParameters['resourceNameValueIt'] = "Permalink opendata.swiss"
        _onLineNodeParameters['resourceNameValueEn'] = "Permalink opendata.swiss"
        _onLineNodeParameters['resourceNameValueRm'] = ""
        _onLineNodeParameters['protocol'] = self.__loginData.protocol.get()
        return _onLineNodeParameters
    
    
    def __updatingRecords(self, uuidsAndRelatedOdsIdentifiersList :list):
        """ updating all MDs with the given uuids from the list
    
        sessionCalls: current API session-object to send requests by using the GeoNetwork REST API
        uuidsAndRelatedIdentifiersList: list with dictionaries which have the keywords uuid and relatedValue
    
        return: the number of updated MD-records as string
        """
        _addCounter = 0
        self.writeLog("****************************************************************************************************************************")
        self.writeLog("now, add onLineResources. at first time check if isUpdateToMui and an online resource with the given protocol exist ")
        self.writeLog("****************************************************************************************************************************")
        _countOfMDs = str(len(uuidsAndRelatedOdsIdentifiersList))
        for uuidAndRelatedOdsIdentifier in uuidsAndRelatedOdsIdentifiersList:
            _index = str(uuidsAndRelatedOdsIdentifiersList.index(uuidAndRelatedOdsIdentifier) + 1)
            if self.__isUpdateToMui:
                self.writeLog(_index + "/" + _countOfMDs + ") check if isUpdateToMui and hasOnlineResource are true, than add xml-Node >onLine<")
            else:
                self.writeLog(_index + "/" + _countOfMDs + ") add xml-Node >onLine<")
            if self.__isUpdateToMui and self.__funcLib.hasOnlineResource(uuidAndRelatedOdsIdentifier.get('uuid'), self.__loginData.protocol.get()):
                self.writeLog("     isUpdateToMui and hasOnlineResource are true, now try to delete it")
                self.__funcLib.deleteOnlineResourceWithGivenProtocol(self.__loginData.protocol.get(), uuid=uuidAndRelatedOdsIdentifier.get('uuid'))
            _onLineNodeParameters = self.__getOnLineNodeParameters(uuidAndRelatedOdsIdentifier.get('relatedValue'))
            _addCounter += self.__funcLib.addXmlOnLineNode(uuidAndRelatedOdsIdentifier, _onLineNodeParameters)
        return str(_addCounter)
    
    def main(self):
        self.writeLog("Script: " + self.__batchName + " has started on environment: " + self.__loginData.environment.get())
        self.__sessionCalls = API.GeocatSession(self.__loginData.urlPrefix, "eng/info?type=me", self.__loginData.username.get(), self.__loginData.password.get())
        self.__requestCalls = API.GeocatRequests(self.__loginData.urlPrefix, self.__loginData.username.get(), self.__loginData.password.get())
        self.__funcLib.setApiCalls(self.__sessionCalls, self.__requestCalls)
        self.writeLog("****************************************************************************************************************************")
        self.writeLog("create a list with all uuids from MDs, which have an onLine resource with the protocol >" + self.__loginData.protocol.get() + "<")
        self.writeLog("****************************************************************************************************************************")
        _mdRecordsAsXmlTree = self.__funcLib.getResponseAsXmlTree("&protocol=" + self.__loginData.protocol.get(), self.__mainLanguage)
        _uuidsList = _mdRecordsAsXmlTree.findall(".//uuid")
        # todo dispatcher
        if self.__loginData.backupMode.get() == "Restore":
            self.__funcLib.doRestor(self.__batchName)
        if self.__loginData.batchEditMode == "delete":
            self.__funcLib.deleteOnlineResourceWithGivenProtocol(self.__loginData.protocol.get(), uuidsList=_uuidsList, uuid="")
        elif self.__loginData.batchEditMode == "add":
            if not self.__isUpdateToMui:
                # uuids of MDs, which has allready a permalink is necessary to remove it from _uuidsList
                _usedUuidsList = self.__funcLib.removeUnusedUuids(_uuidsList, self.__loginData.keyword.get(), self.__mainLanguage)
            else:
                _searchConditionValue = "&keyword=" + self.__loginData.keyword.get() + const.searchFilter + const.plus + const.isNotHarvested + const.plus + const.isMetadataType
                _usedUuidsList = self.__funcLib.getResponseAsXmlTree(_searchConditionValue, mainLanguage).findall(".//uuid")
            _uuidAndIdentifierPairsList = self.__getUuidAndIdentifierPairsList(_usedUuidsList)
            isBackup = self.__loginData.isBackup.get()
            if isBackup:
                _uuidsBakupList = []
                for uuid in _uuidAndIdentifierPairsList:
                    _uuidsBakupList.append(uuid['uuid'])
                self.__funcLib.doBackups(_uuidsBakupList, self.__batchName)
            _updatedRecords = self.__updatingRecords(_uuidAndIdentifierPairsList)
            self.writeLog(_updatedRecords + " online resources was added (MD records updated)")
    
try:
    permaLink2opendata = PermaLink2opendata()     # create the permaLink2opendata-object
    permaLink2opendata.main()                      # call the main-function 
    permaLink2opendata.closeLogFile()
except Exception as error:
    permaLink2opendata.writeLog("Error: " + str(error.args))