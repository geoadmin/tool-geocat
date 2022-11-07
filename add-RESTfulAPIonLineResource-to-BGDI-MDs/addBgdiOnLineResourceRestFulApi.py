
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

class AddBgdiOnLineResourceRestFulApi():
    '''
    ------------------------------------------------------------------------------------------------------------------------
    Autor:      Reithmeier Martin (rem) in 2021 

    Purpose:    This script add one onLine resource with the "RestFul-API geo.admin.ch-Link 
                as service to the record with the given uuid"

    Remarks:    
    ------------------------------------------------------------------------------------------------------------------------
    '''
    # Attributes
    __funcLib = funcLib.FunctionLibrary()
    __loginData = GUI.LoginGUI()
    __batchName = Path(__file__).stem
    __sessionCalls = None
    __requestCalls = None
    __isNeedToRemoveOlrWithGeneralLinks = False

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

    def __removeOnLineResourceWithGeneralLink(self, uuidsList :ElementTree.Element):
        """ delete the onLine Resource whitch have a service link like https://api3.geo.admin.ch
        :uuid: the MD uuid
    
        :return: the count of removed onLine Resource 
        """
        def isOnLineResourceHasGeneralLink(uuid :str):
            """ this function check, if the current MD with the given uuid has an url with general information 
            :uuid: the MD uuid
    
            :return: True if exist otherwise False 
            """
            _distributionXmlNode = self.__funcLib.getDistributionNodeAsRoot(uuid)
            _allDefaultUrls = _distributionXmlNode.findall(".//gmd:onLine//gmd:URL", const.ns)
            _isExist = False
            for url in _allDefaultUrls:
                _urlValue = url.text
                if _urlValue == "https://api3.geo.admin.ch":
                    _isExist = True
                    break
                else:
                    _isExist = False
            return _isExist
    
        self.writeLog("****************************************************************************************************************************")
        self.writeLog("remove all uuids from MDs, which have an onLine resource with the service-link like >https://api3.geo.admin.ch<")
        self.writeLog("****************************************************************************************************************************")
        _removeCounter = 0
        for uuid in uuidsList:
            _countOfMDs = str(len(uuidsList))
            self.writeLog(str(uuidsList.index(uuid) + 1) + "/" + _countOfMDs + ") check onLineResource has a generalLink on MD uuid: " + uuid.text)
            if isOnLineResourceHasGeneralLink(uuid.text):
                self.__funcLib.deleteOnlineResourceWithGivenProtocol(self.__loginData.protocol.get(), uuid=uuid.text)
                _removeCounter += 1
        return _removeCounter
    
    def __getOnLineNodeParameters(self, relatedValue :str):
        _onLineNodeParameters = {}
        _onLineNodeParameters['urlValueDe'] = const.restFulApiUrlPrefix + relatedValue
        _onLineNodeParameters['urlValueFr'] = const.restFulApiUrlPrefix + relatedValue
        _onLineNodeParameters['urlValueIt'] = const.restFulApiUrlPrefix + relatedValue
        _onLineNodeParameters['urlValueEn'] = const.restFulApiUrlPrefix + relatedValue
        _onLineNodeParameters['urlValueRm'] = const.restFulApiUrlPrefix + relatedValue
        _onLineNodeParameters['resourceNameValueDe'] = "RESTful API von geo.admin.ch"
        _onLineNodeParameters['resourceNameValueFr'] = "RESTful API de geo.admin.ch"
        _onLineNodeParameters['resourceNameValueIt'] = "RESTful API da geo.admin.ch"
        _onLineNodeParameters['resourceNameValueEn'] = "RESTful API from geo.admin.ch"
        _onLineNodeParameters['resourceNameValueRm'] = "RESTful API dad geo.admin.ch"
        _onLineNodeParameters['protocol'] = self.__loginData.protocol.get()
        return _onLineNodeParameters
    
    def __isNotBadRequest(self, uuidTechLayerPair :dict):
        """ check if the service-url gives not a bad request
        :uuidTechLayerPair: dictionary with the values of uuid and relatedValue (techLayer)
    
        :return: True if status_code = 200 otherwise False
        """
        _url = const.restFulApiUrlPrefix + uuidTechLayerPair.get('relatedValue')
        _response = requests.get(_url, proxies=const.proxyDict, verify=False)
        if _response.status_code == 200:
            return True
        else:
            _text = _response.text
            _lines = _text.splitlines()
            _outText = ""
            for line in _lines:
                if line:
                    _outText += line + ": "
            self.writeLog("    " + _outText + "\n                               no online resource added in MD " + uuidTechLayerPair.get('uuid'))
            return False
    
    def __updatingRecords(self, uuidAndTechLayerPairsList :list):
        """ updating all MDs with the given uuids from the list
        uuidsIdentifiersList:
    
        return: the number of updated MD records as string
        """
        _addCounter = 0
        self.writeLog("****************************************************************************************************************************")
        self.writeLog("now, add onLineResources if isNotBadRequest")
        self.writeLog("****************************************************************************************************************************")
        _countOfMDs = str(len(uuidAndTechLayerPairsList))
        for uuidAndTechlayerPair in uuidAndTechLayerPairsList:
            self.writeLog(str(uuidAndTechLayerPairsList.index(uuidAndTechlayerPair) + 1) + "/" + _countOfMDs + ") add xml-Node >onLine<")
            if self.__isNotBadRequest(uuidAndTechlayerPair):
                _onLineNodeParameters = self.__getOnLineNodeParameters(uuidAndTechlayerPair.get('relatedValue'))
                _addCounter += self.__funcLib.addXmlOnLineNode(uuidAndTechlayerPair, _onLineNodeParameters)
        return str(_addCounter)
    
    def main(self):
        """ logical main sequence """
        self.writeLog("Script: " + self.__batchName + " has started on environment: " + self.__loginData.environment.get())
        self.__sessionCalls = API.GeocatSession(self.__loginData.urlPrefix, "eng/info?type=me", self.__loginData.username.get(), self.__loginData.password.get())
        self.__requestCalls = API.GeocatRequests(self.__loginData.urlPrefix, self.__loginData.username.get(), self.__loginData.password.get())
        self.__funcLib.setApiCalls(self.__sessionCalls, self.__requestCalls)
        self.writeLog("****************************************************************************************************************************")
        self.writeLog("create a list with all uuids from MDs, which have an onLine resource with the protocol >" + self.__loginData.protocol.get() + "<")
        self.writeLog("****************************************************************************************************************************")
        _geocatUuidsList = self.__funcLib.getResponseAsXmlTree("&protocol=" + self.__loginData.protocol.get(), self.__mainLanguage).findall(".//uuid")
        # todo dispatcher
        isBackup = self.__loginData.isBackup.get()
        if self.__loginData.backupMode.get() == "Restore":
            self.__funcLib.doRestor(self.__batchName)
        if self.__loginData.batchEditMode == "delete":
            self.__funcLib.deleteOnlineResourceWithGivenProtocol(self.__loginData.protocol.get(), uuidsList=_geocatUuidsList, uuid="")
        elif self.__loginData.batchEditMode == "add":
            # needed only at first time to run this script on PROD, now it is not used
            #if self.__isNeedToRemoveOlrWithGeneralLinks:
            #    _removedOnlineResources = self.__removeOnLineResourceWithGeneralLink(_geocatUuidsList)
            #    self.writeLog("Removed onLine resources: " + str(_removedOnlineResources))
            #    _geocatUuidsList.clear()
            #    self.writeLog("****************************************************************************************************************************")
            #    self.writeLog("again: create a list with all uuids from MDs, which have an onLine resource with the protocol >" + self.__loginData.protocol.get() + "< (!! BFE !!)")
            #    self.writeLog("****************************************************************************************************************************")
            #    _geocatUuidsList = self.__funcLib.getResponseAsXmlTree("&protocol=" + self.__loginData.protocol.get(), self.__mainLanguage).findall(".//uuid")
            _usedUuidsList = self.__funcLib.removeUnusedUuids(_geocatUuidsList, self.__loginData.keyword.get(), self.__mainLanguage)
            _uuidAndTechLayerPairsList = self.__funcLib.getUuidAndRelatedTechLayerPairs(_usedUuidsList, self.__loginData.dataSource.get())
            if isBackup:
                _uuidsBakupList = []
                for uuid in _uuidAndTechLayerPairsList:
                    _uuidsBakupList.append(uuid.get('uuid'))
                self.__funcLib.doBackups(_uuidsBakupList, self.__batchName)
            _updatedRecords = self.__updatingRecords(_uuidAndTechLayerPairsList)
            self.writeLog("****************************************************************************************************************************")
            self.writeLog("---finish---  total " + _updatedRecords + " online resources was added")
            self.writeLog("****************************************************************************************************************************")
    
try:
    addBgdiOnLineResourceRestFulApi = AddBgdiOnLineResourceRestFulApi()     # create the permaLink2opendata-object
    addBgdiOnLineResourceRestFulApi.main()                      # call the main-function 
    addBgdiOnLineResourceRestFulApi.closeLogFile()
except Exception as error:
    addBgdiOnLineResourceRestFulApi.writeLog("Error: " + str(error.args))