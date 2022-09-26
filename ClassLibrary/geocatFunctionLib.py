# -*-
import xml.etree.ElementTree as ElementTree
import datetime as TimeStamp
import requests
import json
import os
from pathlib import Path
import geocatConstants as const
import geocatApiCalls as API

class FunctionLibrary:
    """
    swisstopo geocat function Library
    the functions in this module are generalized and can be use in other projects
    """

    __sessionCalls = None
    __requestCalls = None

    def __init__(self):
        self.__logFile = None

    def setLogFile(self, logFile):
        """ it is need to know the reference of the logFile object in this modul

        :logFile: the current logFile object
        """
        #global _logFile
        self.__logFile = logFile

    def setApiCalls(self, sessionCalls :API.GeocatSession, requestCalls :API.GeocatRequests):
        self.__sessionCalls = sessionCalls
        self.__requestCalls = requestCalls

    def writeLog(self, logValue: str):
        """ write logging-informations to file and screen with a timestamp

        :logValue: the string with the data, which you want to log
        """
        if logValue:
            logString = TimeStamp.datetime.now().strftime("%Y-%m-%d-%H:%M.%S%f") + ": " + logValue
        else:
            logString = TimeStamp.datetime.now().strftime("%Y-%m-%d-%H:%M.%S%f") + ": logValue doesn't exist!"
        print(logString)
        self.__logFile.write(logString + "\r")
        self.__logFile.flush()

    def openLogFile(self, loginData, batchName :str):
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
        _timeStamp = TimeStamp.datetime.now().strftime("%Y-%m-%d-%H%M")
        _editMode = loginData.editMode.get()
        # defines the filename of the logfile
        _logFileName = _timeStamp + "][" + loginData.environment.get() + "]" + const.batchEditModeDict[_editMode] + "-" + batchName + ".log"
        # set the full path to the logFile and open it
        if loginData.environment.get() == "PROD":
            _logFileFullPath = "q:/logFiles/PROD/" + _logFileName
        else:
            _logFilePath = "q:/logFiles"
            _logFileFullPath = "q:/logFiles/" + _logFileName
            if not os.path.exists(Path(_logFilePath)):
                _logFileFullPath = "C:/Users/" + os.getlogin() + "/source/repos/logFiles/" + _logFileName
        return  open(_logFileFullPath, 'a+')

    def setMainLanguage(self, language :str):
        """ set the main and second language 
        possible values are: ger or fre
        """
        _mainLanguage = language
        if _mainLanguage == "ger":
            _secondLanguage = "fre"
        elif _mainLanguage == "fre":
            _secondLanguage = "ger"
        else:
            self.writeLog("ERROR - you must either chose \"ger\" or \"fre\" as mainLanguage")
            sys.exit()
        return _mainLanguage, _secondLanguage

    def formatResponse(self, response):
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
            else:
                message = response.text
            return "    responseMessage = " + message
        elif response.status_code == 400:
            return response.text

    def getDistributionNodeAsRoot(self, uuid :str):
        """ get the xml_Distribution-Node as root from the MD with the given uuid
        :uuid: uuid from the MD-record

        :return: the xml-gmd:MD_Distribution node as ElementTree.Element
        """
        #sessionCalls.setApplicationInHeadersTo("xml")
        #recordUrl = "api/0.1/records/" + uuid
        #respons = sessionCalls.sendGetRequest(recordUrl)
        #sessionCalls.setApplicationInHeadersTo("json")
        xmlElementTree = ElementTree.fromstring(self.getMdRecordAsXml(uuid))
        root = xmlElementTree.find(".//gmd:MD_Distribution", const.ns)
        if not root:
            root = xmlElementTree
        return root

    def getMdRecordAsXml(self, uuid :str):
        """ get the MD record as xml from the given uuid
        :sessionCalls: current API session-object
        :uuid: uuid from the MD

        :return: the MD xml in binary format
        """
        self.__sessionCalls.setApplicationInHeadersTo("xml")
        _respons = self.__sessionCalls.sendGetRequest("api/0.1/records/" + uuid)
        while not hasattr(_respons, 'content'):
            _respons = self.__sessionCalls.sendGetRequest("api/0.1/records/" + uuid)
        _responsContent = _respons.content
        self.__sessionCalls.setApplicationInHeadersTo("json")
        return _responsContent

    def getMdRecordDetails(self, uuid :str, batchName :str, isReadFromFile=False, isBackup=False, isRepair=False):
        """ 
        Purpose:
        this methode gets the mdRecord additional details information as dict
        """
        _mdRecordDetails = {}
        if isReadFromFile:
            _uuidBackupPath = const.backupPath.joinpath(batchName)
            with open(_uuidBackupPath.joinpath(uuid + ".json")) as jsonFp:
                _mdRecordDetailsAsJson = json.load(jsonFp)
            jsonFp.close()
        else:
            if isRepair:
                _recordUrl = "https://www.geocat.ch/geonetwork/srv/ger/q?from=1&to=100&fast=index&_content_type=json&uuid=" + uuid
            else:
                _recordUrl = "ger/q?from=1&to=100&fast=index&_content_type=json&uuid=" + uuid
            response = self.__requestCalls.sendGetRequest(_recordUrl)
            _mdRecordDetailsAsJson = response.json()
        if isBackup:
            return _mdRecordDetailsAsJson
        else:
            # check if the count of this request is equal '1', if it '0' -> no mdRecord exist for this uuid
            if _mdRecordDetailsAsJson['summary']['@count'] == "1":
                try:
                   __groupOwner = _mdRecordDetailsAsJson['metadata']['groupOwner']
                except KeyError:
                    _recordUrl = "https://www.geocat.ch/geonetwork/srv/ger/q?from=1&to=100&fast=index&_content_type=json&uuid=" + uuid
                    response = self.__requestCalls.sendGetRequest(_recordUrl)
                    _mdRecordDetailsAsJson = response.json()

                _categories = []
                # check if the keyword 'category' in _mdRecordDetailsAsJson exist
                try:
                    # if more than one category is given, use the extend() method to append categories
                    if type(_mdRecordDetailsAsJson['metadata']['category']) is list:
                        tempList = []
                        tempList.extend(_mdRecordDetailsAsJson['metadata']['category'])
                        for category in tempList:
                            # appends category id and not it's name
                            _categories.append(const.categoryDict[category])
                    else: # use the append() method
                        _categories.append(const.categoryDict[_mdRecordDetailsAsJson['metadata']['category']])
                except KeyError:
                    self.writeLog("    KeyError: the key category doesn\'t exist, no category was assigned")
                _publishedForGroups = []
                try:
                    if type(_mdRecordDetailsAsJson['metadata']['publishedForGroup']) is list:
                        _publishedForGroups.extend(_mdRecordDetailsAsJson['metadata']['publishedForGroup'])
                    else:
                        _publishedForGroups.append(_mdRecordDetailsAsJson['metadata']['publishedForGroup'])
                except KeyError:
                    self.writeLog("    KeyError: the key publishedForGroup doesn\'t exist, it isn\'t published to any Group")

                _mdRecordDetails['categories'] = _categories
                _mdRecordDetails['isPublishedToAll'] = _mdRecordDetailsAsJson['metadata']['geonet:info']['isPublishedToAll']
                _mdRecordDetails['valid'] = _mdRecordDetailsAsJson['metadata']['valid']
                _mdRecordDetails['publishedForGroup'] = _publishedForGroups
                _mdRecordDetails['ownerId'] = _mdRecordDetailsAsJson['metadata']['owner']
                _mdRecordDetails['groupId'] = _mdRecordDetailsAsJson['metadata']['groupOwner']
                return _mdRecordDetails
            else: # _mdRecordDetailsAsJson['summary']['@count'] == "0"
                self.writeLog("MD Record with uuid = " + uuid + " doesn't exist")
                return _mdRecordDetails

    def doBackups(self, uuidsList, batchName :str):
        """ this methode create the backupfolder with the name batchName if it not exist
        write one backup-file in xml-format and one with additional information in json-format 
        for all MDs with the given uuids in uuidsList
        :uuidsList: the list with all uuids of the MDs that need a backup
        :batchName: the name of the current script
        """
        _uuidBakupsPath = const.backupPath.joinpath(batchName)
        if not _uuidBakupsPath.exists():
            _uuidBakupsPath.mkdir(parents=True, exist_ok=True)
        _countOfMDs = str(len(uuidsList))
        for uuid in uuidsList:
            self.writeLog(str(uuidsList.index(uuid) + 1) + "/" + _countOfMDs + ") write backup from MD " + uuid)
            _uuidJsonFilePath = _uuidBakupsPath.joinpath(uuid + ".json")
            _mdRecordDetailsAsJson = self.getMdRecordDetails(uuid, batchName, isBackup=True)
            _uuidJsonFilePath.write_bytes(json.dumps(_mdRecordDetailsAsJson).encode('utf-8'))
            _uuidXmlFilePath = _uuidBakupsPath.joinpath(uuid + ".xml")
            _uuidXmlFilePath.write_bytes(self.getMdRecordAsXml(uuid))

    def doRestor(self, batchName :str):
        """
        """
        _uuidRestorPath = const.backupPath.joinpath(batchName)
        _listDir = os.listdir(_uuidRestorPath)
        _uuidsList = []
        for file in _listDir:
            if file.endswith(".xml"):
                _uuidsList.append(Path(file).stem)
        _countOfMDs = str(len(_uuidsList))
        for uuid in _uuidsList:
            _mdRecordDetails = self.getMdRecordDetails(uuid, batchName, isReadFromFile=True)
            for prefix, uri in const.ns.items():
                ElementTree.register_namespace(prefix, uri)
            with open(_uuidRestorPath.joinpath(uuid + ".xml"), 'r', encoding='UTF-8') as xmlFp:
                uuidXmlString = xmlFp.read()
            xmlFp.close()
            _uuidTreeFromList = ElementTree.fromstring(uuidXmlString)
            _value = ElementTree.tostring(_uuidTreeFromList, encoding='utf-8')
            self.writeLog(str(_uuidsList.index(uuid) + 1) + "/" + _countOfMDs + " restore uuid: " + uuid)
            _response = self.addMdRecordFromXmlFragment(_mdRecordDetails['categories'], _mdRecordDetails['isPublishedToAll'], _value)
            self.writeLog(self.formatResponse(_response))
            self.updateOwnerShipData(uuid, _mdRecordDetails)
            if _mdRecordDetails['valid'] in ('-1', '1'):
                self.validatMdRecord( uuid)
            self.updateMdRecordSharingSettings(uuid, _mdRecordDetails, isRepair=False)

    def addMdRecordFromXmlFragment(self, categories :list, isPublishToAll :str, value ):
        """"""
        _metadataType = "metadataType=METADATA"
        _recursiveSearch = "&recursiveSearch=false"
        _publishToAll = "&publishToAll=" + isPublishToAll
        _assignToCatalog = "&assignToCatalog=false"
        _uuidProcessing = "&uuidProcessing=OVERWRITE"
        _category = ""
        for categoryId in categories:
            _category += "&category=" + str(categoryId)
        _rejectIfInvalid = "&rejectIfInvalid=false"
        _transformWith = "&transformWith=_none_"
        self.writeLog("      value: " + str(value))
        urlValue = "api/0.1/records?" + _metadataType + _recursiveSearch + _publishToAll + _assignToCatalog + _uuidProcessing + _category + _rejectIfInvalid + _transformWith
        self.writeLog("      urlValue: " + urlValue)
        return self.__sessionCalls.sendPutRequest(urlValue, value, xpath="")

    def updateOwnerShipData(self, uuid, mdRecordDetails):
        """
        """
        self.writeLog("    set mdRecords group and owner")
        urlValue = "api/0.1/records/" + uuid + "/ownership?groupIdentifier=" + mdRecordDetails['groupId'] + "&userIdentifier=" + mdRecordDetails['ownerId'] + "&approved=true"
        self.writeLog("      urlValue: " + urlValue)
        response = self.__sessionCalls.sendPutRequest(urlValue, value="", xpath="")
        if response.status_code == 201:
            self.writeLog("    group and owner from mdRecord " + uuid + " updated")
        else:
            self.writeLog("    !! group and owner from mdRecord " + uuid + " not updated")

    def getMdRecordPrivilegeSetting(self, uuid, isRepair=False):
        """"""
        self.writeLog("    get mdRecords privilege settings")
        if isRepair:
            urlValue = "https://www.geocat.ch/geonetwork/srv/api/0.1/records/" + uuid + "/sharing"
        else:
            urlValue = "api/0.1/records/" + uuid + "/sharing"
        self.writeLog("      urlValue: " + urlValue)
        return self.__sessionCalls.sendGetRequest(urlValue)

    def updateMdRecordSharingSettings(self, uuid, mdRecordDetails, isRepair):
        """"""
        def _setMdRecordPrivilege(uuid, groupId, operations):
            """"""
            shares = {'clear': False, 'privileges': [{'group': groupId , 'operations': operations}]}
            self.writeLog("      privilage settings: " + str(shares))
            urlValue = "api/0.1/records/" + uuid + "/sharing"
            value=json.dumps(shares)
            return self.__sessionCalls.sendPutRequest(urlValue, value, xpath="")

        def _writeLog():
            """"""
            self.writeLog("     mdRecord privileges updated")

        def _setPrivilegeOfGroupOwner(prevelege):
            """"""
            _response = _setMdRecordPrivilege(sessionCalls, uuid, mdRecordDetails['groupId'], privilege['operations'])
            _writeLog()

        self.writeLog("     update mdRecord privileges")
        _recordSharingSettingsAsJson = json.loads(self.getMdRecordPrivilegeSetting(uuid, isRepair).text)
        if len(mdRecordDetails['publishedForGroup']) > 1:
            for privilege in _recordSharingSettingsAsJson['privileges']:
                if privilege['group'] == 0:
                    _response = _setMdRecordPrivilege(uuid, '0', privilege['operations'])
                    _writeLog()
                elif privilege['group'] == 1:
                    _response = _setMdRecordPrivilege(uuid, '1', privilege['operations'])
                    _writeLog()
                elif privilege['group'] == int(mdRecordDetails['groupId']):
                    _setPrivilegeOfGroupOwner(privilege)
        else:
            for privilege in _recordSharingSettingsAsJson['privileges']:
                if privilege['group'] == int(mdRecordDetails['groupId']):
                    _setPrivilegeOfGroupOwner(privilege)

    def validatMdRecord(self, uuid):
        """"""
        self.writeLog("    validate the mdRecord")
        urlValue = "api/0.1/records/validate?uuids=" + uuid
        self.writeLog("      urlValue: " + urlValue)
        response = self.__sessionCalls.sendPutRequest(urlValue, value="", xpath="")
        self.writeLog(self.formatResponse(response))

    def removeEmptyTransferOptionsNode(self, uuid :str, xpath :str):
        """ remove an empty transferOptions node
        :uuid: uuid from the MD
        :xpath: the path to the Xml-Node

        :return: 1 if the node was deleted, otherwise 0
        """
        value = "<gn_delete></gn_delete>"
        self.writeLog("      value: " + value)
        self.writeLog("      xpath: " + xpath)
        urlValue = "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=true"
        self.writeLog("      urlValue: " + urlValue)
        response = self.__sessionCalls.sendPutRequest(urlValue, value, xpath)
        responseMessage = self.formatResponse(response)
        self.writeLog(responseMessage)
        if "Info:" in responseMessage:
            return 1
        else:
            return 0

    def getCountOfTransferOptionsNodes(self, uuid :str):
        """ get the count of transferoptions-nodes, from the MD with the given uuid
        first, checks if there are empty transferoptions-nodes and remove it from MD

        :uuid: uuid from the MD

        :return: the number of xml-transferoptions nodes, which are not empty
        """
        distribution = self.getDistributionNodeAsRoot(uuid)
        if distribution.tag == "{http://www.isotc211.org/2005/gmd}MD_Distribution":
            xmlTransferOptionsNodes = distribution.findall(".//gmd:transferOptions", const.ns)
            self.writeLog("    check if has empty tronsferOptions nodes and remove it if exist")
            removed = 0
            for transferOptions in reversed(xmlTransferOptionsNodes):
                dto = transferOptions.find("./gmd:MD_DigitalTransferOptions", const.ns)
                if not dto:
                    self.writeLog("      remove empty transferOptionsNode[" + str(xmlTransferOptionsNodes.index(transferOptions) + 1) + "]/" + str(len(xmlTransferOptionsNodes)))
                    xpath = ".//gmd:transferOptions[" + str(xmlTransferOptionsNodes.index(transferOptions) + 1) + "]"
                    removed += self.removeEmptyTransferOptionsNode(uuid, xpath)
            self.writeLog("      removed " + str(removed) + " empty transferOptionsNodes")
            distribution = None
            xmlTransferOptionsNodes = None
            distribution = self.getDistributionNodeAsRoot(uuid)
            xmlTransferOptionsNodes = distribution.findall(".//gmd:transferOptions", const.ns)
            counter = len(xmlTransferOptionsNodes)
            return str(counter)
        else:
            return str(-1)

    def hasOnlineResource(self, uuid :str, protocol :str):
        """ check if an online resource with the given protocol exist
        :uuid: uuid from the MD
        :protocol: the protocol name where you search from

        :return: true if exist, otherwise false
        """
        xpath = ".//gmd:onLine//gmd:protocol/gco:CharacterString"
        isExist = False
        distribution = self.getDistributionNodeAsRoot(uuid)
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

    def getResponseAsXmlTree(self, searchValue :str, mainLanguage :str, start="1", end="1500"):
        """ get the response of the corresponding search condition as xml tree 

        :searchValue: the search condition eg. &keyword=keywordValue
        :mainLanguage: the defined main language
        :start: from which MD will be start the search request
        :end: to which MD will be end the search request

        :return: a element with all nodes whitch corresponding the search condition
        """
        self.writeLog("    get the response of the corresponding search condition: /q?from=" + start + "&to=" + end + searchValue)
        urlValue = mainLanguage + "/q?from=" + start + "&to=" + end + searchValue
        response = self.__requestCalls.sendGetRequest(urlValue)
        while response.status_code != 200:
            response = self.__requestCalls.sendGetRequest(urlValue)
        countOfMDs = ElementTree.fromstring(response.content).find("./summary").attrib["count"]
        self.writeLog("    Number of MDs corresponding to your search: " + countOfMDs)
        xmlElementTree = ElementTree.fromstring(response.content)
        return xmlElementTree

    def removeUnusedUuids(self, uuidsList :ElementTree.Element, keyword :str, mainLanguage :str):
        """ return a list with all uuids which use to add the opendata.swiss permalink to geocat MDs
        if the keyword uuid not in the protocol uuid then add it to the result list
        :uuidsList: a list with all MD uuids which have the given protocol

        :return: a list with all MD uuids which haven't the given protocol
        """
        self.writeLog("****************************************************************************************************************************")
        self.writeLog("create a list with all uuids from MDs, which have the keyword >" + keyword + "<")
        self.writeLog("****************************************************************************************************************************")
        searchConditionValue = "&keyword=" + keyword + const.notHarvested + const.isMetadataType #+ const.isValid
        keywordUuidsList =  self.getResponseAsXmlTree(searchConditionValue, mainLanguage).findall(".//uuid")
        protocolUuidsList = uuidsList
        isEqual = False
        resultList = []
        self.writeLog("****************************************************************************************************************************")
        self.writeLog("remove all uuids from keywordList, which have the same uuid in protocolList")
        self.writeLog("****************************************************************************************************************************")
        for keywordUuid in keywordUuidsList:
            for porotocolUuid in protocolUuidsList:
                if keywordUuid.text == porotocolUuid.text:
                    isEqual = True
                    break
            if not isEqual:
                resultList.append(keywordUuid)
            else:
                isEqual = False
        self.writeLog("the list with all needed uuid-Elements was created and has " + str(len(resultList)) + " elements")
        return resultList

    def getValueAttribute(self, transferOptionsNumber :int, onLineNodeParameters :dict):
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
        codeListValue = onLineNodeParameters['function']
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
        if codeListValue:
            functionBlock = "<gmd:function><gmd:CI_OnLineFunctionCode codeList='http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/codelist/ML_gmxCodelists.xml#CI_OnLineFunctionCode' codeListValue='" + codeListValue + "'/></gmd:function>"
        else:
            functionBlock = ""
        onlineResourceBlock = "<gmd:CI_OnlineResource>" + linkageBlock + protocolBlock + resourceNameBlock + resourceDescriptionBlock + functionBlock + "</gmd:CI_OnlineResource>"
        buildedResourceType = resourceTypeTag + onlineResourceBlock + resourceTypeCloseTag
        if transferOptionsNumber > 0:
            return batchEditModeTag + buildedResourceType + batchEditModeCloseTag
        else:
            return batchEditModeTag + "<gmd:MD_DigitalTransferOptions " + const.namespaces + ">" + buildedResourceType + "</gmd:MD_DigitalTransferOptions>" +  batchEditModeCloseTag

    def addXmlOnLineNode(self, relatedValues :dict, onLineNodeParameters :dict):
        """ main function to add <gmd:onLine> ... </gmd:onLine> 

        :relatedValues: {"uuid" : "value", "relatedValue" : "value"} data pair: uuid with the related value 
        :onLineNodeParameters: onLineNode values, which are different for each MD-record 

        :return:
        """
        transferOptionsNodeCount = self.getCountOfTransferOptionsNodes(relatedValues['uuid'])
        # need if <gmd:distributionInfo> node not exist
        if int(transferOptionsNodeCount) == -1:
            value = "<gn_add><gmd:distributionFormat " + const.namespaces + " xlink:href='local://srv/api/registries/entries/388d711d-c1ea-49ea-a02d-5868b1174b55?lang=ger,fre,eng,ita&amp;schema=iso19139.che'><gmd:MD_Format><gmd:name><gco:CharacterString>autres formats sur demande / andere Formate auf Anfrage</gco:CharacterString></gmd:name><gmd:version gco:nilReason='missing'><gco:CharacterString/></gmd:version></gmd:MD_Format></gmd:distributionFormat></gn_add>"
            xpath = "/che:CHE_MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution"
            urlValue = "api/0.1/records/batchediting?uuids=" + relatedValues['uuid'] + "&updateDateStamp=true"
            self.writeLog("    MD has no online resource, its need to add additional data")
            self.writeLog("      urlValue: " + urlValue)
            self.writeLog("      value: " + value)
            self.writeLog("      xpath: " + xpath)
            response = self.__sessionCalls.sendPutRequest(urlValue, value, xpath)
            responseMessage = self.formatResponse(response)
            self.writeLog(responseMessage)
            value = "<gn_add><gmd:transferOptions " + const.namespaces + " ></gmd:transferOptions></gn_add>"
            response = sessionCalls.sendPutRequest(urlValue, value, xpath)
            transferOptionsNodeCount = "0"
        value = self.getValueAttribute(int(transferOptionsNodeCount), onLineNodeParameters)
        if int(transferOptionsNodeCount) > 0:
            xpath = "/che:CHE_MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions[" + transferOptionsNodeCount + "]/gmd:MD_DigitalTransferOptions"
        elif int(transferOptionsNodeCount) == 0:
            xpath = "/che:CHE_MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions"
        urlValue = "api/0.1/records/batchediting?uuids=" + relatedValues['uuid'] + "&updateDateStamp=true"
        self.writeLog("    urlValue: " + urlValue)
        self.writeLog("    value: " + value)
        self.writeLog("    xpath: " + xpath)
        response = self.__sessionCalls.sendPutRequest(urlValue, value, xpath)
        responseMessage = self.formatResponse(response)
        self.writeLog(responseMessage)
        if "Info:" in responseMessage:
            return 1
        else:
            return 0

    def getUuidAndRelatedTechLayerPairs(self, uuidsList :list, dataSource :str, inputFilename=""):
        """ return the list with all needed uuid and it's related techLayer pairs 

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
                if "." in geocat_id:
                   dataset_id, geocat_id = uuidTechLayer.split(";")
                if len(geocat_id) == 36:
                    resultLine['uuid'] = geocat_id
                    resultLine['relatedValue'] = dataset_id
                    resultList.append(resultLine)
            return resultList

        for uuid in uuidsList:
            countOfMDs = str(len(uuidsList))
            self.writeLog(str(uuidsList.index(uuid) + 1) + "/" + countOfMDs + ") search related techLayer from uuid: " + uuid.text)
            for layer in responseLayers:
                if uuid.text == layer[idGeoCat]:
                    resultLine = {}
                    resultLine['uuid'] = layer[idGeoCat]
                    resultLine['relatedValue'] = layer[layerBodId]
                    resultList.append(resultLine)
        self.writeLog("the list with all uuid-techLayer pairs was created and has " + str(len(resultList)) + " dictionaries")
        return resultList

    def deleteOnlineResourceWithGivenProtocol(self, protocol :str, **uuids):
        """ remove one or all online resource, which having the given protocol eg. ESRI:REST

        :protocol: the name of the protocol
        :**uuids:
        :uuids['uuid']: only one uuid, use if only one MD record to remove the online resource
        :uuids['uuidsList']: list of uuids, use if more than one MD record to remove the online resource
        """
        value = "<gn_delete></gn_delete>"
        xpath = ".//gmd:onLine[*/gmd:protocol/*/text() = '" + protocol + "']"
        self.writeLog("      value: " + value)
        self.writeLog("      xpath: " + xpath)
        def runTask(uuid :str):
            """ nested function to do the same things of both conditions"""
            urlValue = "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=true"
            self.writeLog("      urlValue: " + urlValue)
            response = self.__sessionCalls.sendPutRequest(urlValue, value, xpath)
            responseMessage = self.formatResponse(response)
            self.writeLog(responseMessage)
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
                self.writeLog(str(uuidsList.index(uuid) + 1) + "/" + countOfMDs + ") delete xml-Node onLine")
                deleteCounter += runTask(uuid.text)
        self.writeLog("      " + str(deleteCounter) + " online resources was deleted")

    def deleteXpath(self, xPath :str, uuid :str):
        value = "<gn_delete></gn_delete>"
        xpath = xPath
        self.writeLog("      value: " + value)
        self.writeLog("      xpath: " + xpath)
        urlValue = "api/0.1/records/batchediting?uuids=" + uuid + "&updateDateStamp=true"
        self.writeLog("      urlValue: " + urlValue)
        response = self.__sessionCalls.sendPutRequest(urlValue, value, xpath)
        responseMessage = self.formatResponse(response)
        self.writeLog(responseMessage)
