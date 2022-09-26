
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

class AddLayerIdToGeocat():
    '''
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

    def __getCitationNodeAsRoot(self, uuid :str):
        """ get the xml_Citation-Node as root from the MD with the given uuid
    
        :uuid: uuid from the MD
    
        :return: the xml-gmd:CI_Citation-node as root
        """
        self.__sessionCalls.setApplicationInHeadersTo("xml")
        _recordUrl = "api/0.1/records/" + uuid
        _respons = self.__sessionCalls.sendGetRequest(_recordUrl)
        self.__sessionCalls.setApplicationInHeadersTo("json")
        return ElementTree.fromstring(_respons.content).find(".//gmd:CI_Citation", const.ns)
    
    def __isTechLayerNameExist(self, uuid :str):
        """ 
        :sessionCalls: current API session-object
        :uuid: uuid from the MD
        """
        _citationXpath = self.__getCitationNodeAsRoot(uuid)
        _identifierXpath = _citationXpath.findall(".//gmd:MD_Identifier", const.ns)
        if _identifierXpath:
            return True
        else:
            return False
    
    def __getUsedUuidsList(self, uuidsList :ElementTree.Element):
        """ 
        :sessionCalls: current API session-object
        :uuidsList: uuids from the MDs
        """
        _countOfMDs = str(len(uuidsList))
        _resultList = []
        for uuid in uuidsList:
            self.writeLog(str(uuidsList.index(uuid) + 1) + "/" + _countOfMDs + ") check if techLayerName exist on MD " + uuid)
            if not self.__isTechLayerNameExist(uuid.text):
                _resultList.append(uuid)
        return _resultList
    
    def __addXmlIdentifierNode(self, uuidTechlayerPair :dict):
        """ """
        def _getValueAttribute(techLayer :str):
            """ build the value-attribute for the batchediting putRequest 
            """
            _batchEditModeTag = "<gn_add>"
            _batchEditModeCloseTag = "</gn_add>"
            _identifierCodeTag = "<gmd:identifier " + const.namespaces + "><gmd:MD_Identifier><gmd:code>"
            _identifierCodeCloseTag = "</gmd:code></gmd:MD_Identifier></gmd:identifier>"
            _layerName = "<gco:CharacterString>" + techLayer + "</gco:CharacterString>"
    
            return _batchEditModeTag + _identifierCodeTag + _layerName + _identifierCodeCloseTag + _batchEditModeCloseTag
    
        _value = _getValueAttribute(uuidTechlayerPair.get('relatedValue'))
        # get the count of the transferoptions tag
        _xpath = "/che:CHE_MD_Metadata/gmd:identificationInfo/che:CHE_MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier[1]"
        _urlValue = "api/0.1/records/batchediting?uuids=" + uuidTechlayerPair['uuid'] + "&updateDateStamp=true"
        self.writeLog("    urlValue: " + _urlValue)
        self.writeLog("    value: " + _value)
        self.writeLog("    xpath: " + _xpath)
        _response = self.__sessionCalls.sendPutRequest(_urlValue, _value, _xpath)
        _responseMessage = self.__funcLib.formatResponse(_response)
        self.writeLog(_responseMessage)
        if "Info:" in _responseMessage:
            return 1
        else:
            return 0
    
    def main(self):
        self.writeLog("Script: " + self.__batchName + " has started on environment: " + self.__loginData.environment.get())
        self.__sessionCalls = API.GeocatSession(self.__loginData.urlPrefix, "eng/info?type=me", self.__loginData.username.get(), self.__loginData.password.get())
        self.__requestCalls = API.GeocatRequests(self.__loginData.urlPrefix, self.__loginData.username.get(), self.__loginData.password.get())
        self.__funcLib.setApiCalls(self.__sessionCalls, self.__requestCalls)
        _uuidAndTechLayerPairsList = self.__funcLib.getUuidAndRelatedTechLayerPairs(None, self.__loginData.dataSource.get(), self.__loginData.inputFilename.get())
        # todo dispatcher
        if self.__loginData.backupMode.get() == "Restore":
            self.__funcLib.doRestor(self.__batchName)
        isBackup = self.__loginData.isBackup.get()
        if isBackup:
            _uuidsBakupList = []
            for uuidTechLayer in _uuidAndTechLayerPairsList:
                _uuidsBakupList.append(uuidTechLayer.get('uuid'))
            self.__funcLib.doBackups(_uuidsBakupList, self.__batchName)
        if self.__loginData.batchEditMode == "add":
            _addCounter = 0
            _countOfMDs = str(len(_uuidAndTechLayerPairsList))
            for uuidAndTechlayerPair in _uuidAndTechLayerPairsList:
                if not self.__isTechLayerNameExist(uuidAndTechlayerPair.get('uuid')):
                    self.writeLog(str(_uuidAndTechLayerPairsList.index(uuidAndTechlayerPair) + 1) + "/" + _countOfMDs + ") add identifier xml-Node in MD: " + uuidAndTechlayerPair.get('uuid'))
                    _addCounter += self.__addXmlIdentifierNode(uuidAndTechlayerPair)
                else:
                    self.writeLog(str(_uuidAndTechLayerPairsList.index(uuidAndTechlayerPair) + 1) + "/" + _countOfMDs + ") identifier xml-Node already exist in MD: " + uuidAndTechlayerPair.get('uuid'))
            self.writeLog(str(_addCounter) + " identifiers was added")
        elif self.__loginData.batchEditMode == "delete":
            _countOfMDs = str(len(_uuidAndTechLayerPairsList))
            for uuidAndTechlayerPair in _uuidAndTechLayerPairsList:
                if self.__isTechLayerNameExist(uuidAndTechlayerPair.get('uuid')):
                    self.writeLog(str(_uuidAndTechLayerPairsList.index(uuidAndTechlayerPair) + 1) + "/" + _countOfMDs + ") delete identifier xml-Node in MD: " + uuidAndTechlayerPair.get('uuid'))
                    self.__funcLib.deleteXpath(".//gmd:identifier", uuidAndTechlayerPair.get('uuid'))
    
try:
    aAddLayerIdToGeocat = AddLayerIdToGeocat()     # create the renameProtocolValue-object
    aAddLayerIdToGeocat.main()                      # call the main-function 
    aAddLayerIdToGeocat.closeLogFile()
except Exception as error:
    aAddLayerIdToGeocat.writeLog("Error: " + str(error.args))