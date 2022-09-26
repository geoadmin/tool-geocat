
import sys
# sys.path.append("..\\ClassLibrary") # is needed when use outside from Visual Studio
import urllib3
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from requests.auth import HTTPBasicAuth
import geocatLoginGUI as GUI
import geocatApiCalls as API
import geocatConstants as const
import geocatFunctionLib as funcLib

# desable the exceptions of InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Remove_BGDI_Keyword_from_list:
    '''
    Autor:      Reithmeier Martin (rem) in 2022

    Purpose:    With this script you can add or delete the keyword {BGDI Bundesgeodaten-Infrastruktur} from MDs with the
                given list of uuids
                The uuid list is given from Veronique Constantin in a excel-sheet

    Remarks:    Write the uuids in a text-file
            

    '''
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

    def __getKeywordNode(self, isThesaurusExist :bool):
        """
        Purpose:
        if the script in add-mode, this method return a xml-node-object from type Element

        Parameter:
            :isThesaurusExist: [bool]
            =True
                need to add the keyword if any keywords exist for geocat
                returns only the keyword-node
            =False
                need to add the keyword if no other keyword exist for geocat
                returns the full descriptiveKeywords-node

        return:
            :xmlFragmentString [Element]
        """
        if isThesaurusExist:
            return ElementTree.fromstring("<gmd:keyword " + const.namespaces + " xsi:type='gmd:PT_FreeText_PropertyType'><gco:CharacterString>BGDI Bundesgeodaten-Infrastruktur</gco:CharacterString><gmd:PT_FreeText><gmd:textGroup><gmd:LocalisedCharacterString locale='#DE'>BGDI Bundesgeodaten-Infrastruktur</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup><gmd:LocalisedCharacterString locale='#FR'>IFDG l’Infrastructure Fédérale de données géographiques</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup><gmd:LocalisedCharacterString locale='#IT'>IFDG Infrastruttura federale dei dati geografici</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup><gmd:LocalisedCharacterString locale='#EN'>FSDI Federal Spatial Data Infrastructure</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup><gmd:LocalisedCharacterString locale='#RM'/></gmd:textGroup></gmd:PT_FreeText></gmd:keyword>")
        else:
            return ElementTree.fromstring("<gmd:descriptiveKeywords " + const.namespaces + "><gmd:MD_Keywords><gmd:keyword xsi:type='gmd:PT_FreeText_PropertyType'><gco:CharacterString>BGDI Bundesgeodaten-Infrastruktur</gco:CharacterString><gmd:PT_FreeText><gmd:textGroup><gmd:LocalisedCharacterString locale='#DE'>BGDI Bundesgeodaten-Infrastruktur</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup><gmd:LocalisedCharacterString locale='#FR'>IFDG l’Infrastructure Fédérale de données géographiques</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup><gmd:LocalisedCharacterString locale='#IT'>IFDG Infrastruttura federale dei dati geografici</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup><gmd:LocalisedCharacterString locale='#EN'>FSDI Federal Spatial Data Infrastructure</gmd:LocalisedCharacterString></gmd:textGroup><gmd:textGroup><gmd:LocalisedCharacterString locale='#RM' /></gmd:textGroup></gmd:PT_FreeText></gmd:keyword><gmd:type><gmd:MD_KeywordTypeCode codeList='http://www.isotc211.org/2005/resources/codeList.xml#MD_KeywordTypeCode' codeListValue='theme' /></gmd:type><gmd:thesaurusName><gmd:CI_Citation><gmd:title><gco:CharacterString>geocat.ch</gco:CharacterString></gmd:title><gmd:date><gmd:CI_Date><gmd:date><gco:Date>2022-01-24</gco:Date></gmd:date><gmd:dateType><gmd:CI_DateTypeCode codeList='http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode' codeListValue='publication' /></gmd:dateType></gmd:CI_Date></gmd:date><gmd:identifier><gmd:MD_Identifier><gmd:code><gmx:Anchor xlink:href='https://geocat-int.dev.bgdi.ch/geonetwork/srv/eng/thesaurus.download?ref=local.theme.geocat.ch'>geonetwork.thesaurus.local.theme.geocat.ch</gmx:Anchor></gmd:code></gmd:MD_Identifier></gmd:identifier></gmd:CI_Citation></gmd:thesaurusName></gmd:MD_Keywords></gmd:descriptiveKeywords>")

    def __checkIsKeywordExist(self, uuid :str, mdRecord :ElementTree.Element):
        """
        Purpose:
        if the script was broken by a proxy-error it is helpfull to know which MD must skip if you run the script again

        Parameter:
            :sessionCalls: [API.geocatSession] current API session-object
            :uuid: [str] the uuid from MD
            :mdRecord: [Element]

        return:
            True if exist otherwise False
        """
        _isExist = False
        # get all thesauruses
        _descriptiveKeywordsList = mdRecord.findall(".//gmd:identificationInfo/che:CHE_MD_DataIdentification/gmd:descriptiveKeywords", const.ns)
        for descriptiveKeywords in _descriptiveKeywordsList:
            _MD_KeywordsAsRoot = descriptiveKeywords.find(".//gmd:MD_Keywords", const.ns)
            if _MD_KeywordsAsRoot:
                _thesaurusNameValue = _MD_KeywordsAsRoot.find(".//gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString", const.ns).text
                if _thesaurusNameValue == "geocat.ch":
                    # get all keywords from the geocat.ch thesaurus
                    _keywords = _MD_KeywordsAsRoot.findall(".//gmd:keyword", const.ns) # findall returns always a list
                    # find the right keyword in the keywordlist
                    for keyword in _keywords:
                        _keywordValue = keyword.find("gco:CharacterString", const.ns).text
                        # check if keywordValue equal the BGDI keyword
                        if _keywordValue == self.__loginData.keyword.get():
                            self.__funcLib.writeLog("     the keyword " + self.__loginData.keyword.get() + " exist")
                            _isExist = True
                            break
        return _isExist

    def __addKeywords(self, uuidsList :list):
        """
        Purpose:
        add the keyword {BGDI Bundesgeodaten-Infrastruktur} to all mdRecord which uuid is in list

        Parameter:
            :gcRequests: [dict] current API session- and request-object
            :uuidsList: [list] all used uuids

        return:
            void
        """
        _isRepair = False
        _addCounter = 0
        _countOfMDs = str(len(uuidsList))
        #need to initialize the ElementTree with the right namespace
        for prefix, uri in const.ns.items():
            ElementTree.register_namespace(prefix, uri)
        for uuid in uuidsList:
            _ok = False
            self.__funcLib.writeLog("MD Record Nr.: " + str(uuidsList.index(uuid) + 1) + "/" + _countOfMDs + " uuid=" + uuid)
            # get the additional detail information from the mdRecord
            _mdRecordDetails = self.__funcLib.getMdRecordDetails(uuid, self.__batchName, isRepair=_isRepair)
            # check if the mdRecord exist
            if _mdRecordDetails:
                _mdRecordAsElement = ElementTree.fromstring(self.__funcLib.getMdRecordAsXml(uuid))
                # check if keyword not exist
                _isKeywordNotExist = not self.__checkIsKeywordExist(uuid, _mdRecordAsElement)
                if _isKeywordNotExist:
                    _MD_KeywordsAsRoot = _mdRecordAsElement.find(".//gmd:identificationInfo/che:CHE_MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords", const.ns)
                    if _MD_KeywordsAsRoot:
                        self.__funcLib.writeLog("    add keyword " + self.__loginData.keyword.get() + "")
                        _MD_KeywordsAsRoot.append(self.__getKeywordNode(isThesaurusExist=True))
                        _ok = True
                    else:
                        _CHE_MD_DataIdentificationAsRoot = _mdRecordAsElement.find(".//gmd:identificationInfo/che:CHE_MD_DataIdentification", const.ns)
                        if _CHE_MD_DataIdentificationAsRoot:
                            _ok = True
                            self.__funcLib.writeLog("add keyword with thesaurus" + self.__loginData.keyword.get() + "")
                            _CHE_MD_DataIdentificationAsRoot.insert(2, self.__getKeywordNode(isThesaurusExist=False))
                    if _ok:
                        _value = ElementTree.tostring(_mdRecordAsElement, encoding='utf8', method='xml')
                        _response = self.__funcLib.addMdRecordFromXmlFragment(_mdRecordDetails['categories'], _mdRecordDetails['isPublishedToAll'], _value)
                        _addCounter += 1
                        self.__funcLib.writeLog(self.__funcLib.formatResponse(_response))
                        self.__funcLib.updateOwnerShipData(uuid, _mdRecordDetails)
                        if _mdRecordDetails['valid'] in ('-1', '1'):
                            self.__funcLib.validatMdRecord(uuid)
                        self.__funcLib.updateMdRecordSharingSettings(uuid, _mdRecordDetails, _isRepair)
                    else:
                        self.__funcLib.writeLog("    keyword " + self.__loginData.keyword.get() + " couldn\'t added")
            else:
                self.__funcLib.writeLog("    !! no detail info found for uuid: " + uuid + " ; mdRecord not exist!!")
        self.__funcLib.writeLog(str(_addCounter) + " keywords " + self.__loginData.keyword.get() + " was added")

    def __removeKeyword(self, mdRecordDetails :dict, mdRecord :ElementTree.Element):
        """
        Purpose:

        Parameter:

        return:
        """
        _isRemoved = False
        # get all thesauri
        _descriptiveKeywordsList = mdRecord.findall(".//gmd:identificationInfo/che:CHE_MD_DataIdentification/gmd:descriptiveKeywords", const.ns)
        for descriptiveKeywords in _descriptiveKeywordsList:
            _MD_KeywordsAsRoot = descriptiveKeywords.find(".//gmd:MD_Keywords", const.ns)
            if _MD_KeywordsAsRoot:
                _thesaurusNameValue = _MD_KeywordsAsRoot.find(".//gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString", const.ns).text
                self.__funcLib.writeLog("     thesaurusName= " + _thesaurusNameValue)
                if _thesaurusNameValue == "geocat.ch":
                    # get all keywords from geocat thesaurus
                    _keywords = _MD_KeywordsAsRoot.findall(".//gmd:keyword", const.ns)
                    # find the right keyword
                    for keyword in _keywords:
                        keywordValue = keyword.find("gco:CharacterString", const.ns).text
                        self.__funcLib.writeLog("     keyword= " + keywordValue)
                        # if keywordValue equal the BGDI keyword -> remove it
                        if keywordValue == self.loginData.keyword.get():
                            self.__funcLib.writeLog("    remove keyword " + self.loginData.keyword.get())
                            _MD_KeywordsAsRoot.remove(keyword)
                            _value = ElementTree.tostring(mdRecord, encoding='utf8')
                            _response = self.__funcLib.addMdRecordFromXmlFragment(mdRecordDetails['categories'], mdRecordDetails['isPublishedToAll'], _value)
                            self.__funcLib.writeLog(self.__funcLib.formatResponse(_response))
                            if _response.status_code == 201:
                                _isRemoved = True
                            break
        if _isRemoved:
            return 1
        else:
            return 0

    def __removeKeywords(self, uuidsList :list):
        """
        Purpose:
        remove the keyword {BGDI Bundesgeodaten-Infrastruktur} from all mdRecord which uuid is in list

        Parameter:
            :gcRequests: [dict] current API session- and request-object
            :uuidsList: [list] all used uuids

        return:
            void
        """
        _removeCounter = 0
        _isRepair=False
        _countOfMDs = str(len(uuidsList))
        for prefix, uri in const.ns.items():
            ElementTree.register_namespace(prefix, uri)
        for uuid in uuidsList:
            if uuidsList.index(uuid) + 1 > 0:
                self.__funcLib.writeLog("MD Record Nr.: " + str(uuidsList.index(uuid) + 1) + "/" + _countOfMDs + " uuid= " + uuid)
                _mdRecordDetails = self.__funcLib.getMdRecordDetails(uuid, self.__batchName, _isRepair)
                if _mdRecordDetails:
                    _mdRecordAsElement = ElementTree.fromstring(self.__funcLib.getMdRecordAsXml(uuid))
                    if _mdRecordAsElement.tag == "apiError":
                        _description = _mdRecordAsElement.find(".//description").text
                        self.__funcLib.writeLog("    apiError: " + _description)
                    else:
                        if self.__checkIsKeywordExist(uuid, _mdRecordAsElement):
                            _removeCounter += self.__removeKeyword(_mdRecordDetails, _mdRecordAsElement)
                            self.__funcLib.updateOwnerShipData(uuid, _mdRecordDetails)
                            if _mdRecordDetails['valid'] in ('-1', '1'):
                                self.__funcLib.validatMdRecord(uuid)
                            self.__funcLib.updateMdRecordSharingSettings(uuid, _mdRecordDetails, _isRepair)
                else:
                    self.__funcLib.writeLog("    !! no detail info found for uuid: " + uuid + " ; mdRecord not exist!!")
        self.__funcLib.writeLog(str(_removeCounter) + " keywords " + self.__loginData.keyword.get() + " was removed")

    def main(self):
        """
        Purpose:

        Parameter:

        return:
        """
        self.__funcLib.writeLog("Script: " + self.__batchName + " has started on environment: " + self.__loginData.environment.get())
        self.__sessionCalls = API.GeocatSession(self.__loginData.urlPrefix, "eng/info?type=me", self.__loginData.username.get(), self.__loginData.password.get())
        self.__requestCalls = API.GeocatRequests(self.__loginData.urlPrefix, self.__loginData.username.get(), self.__loginData.password.get())
        self.__funcLib.setApiCalls(self.__sessionCalls, self.__requestCalls)

        if self.__loginData.backupMode.get() == "Restore":
            self.__funcLib.doRestor(self.__batchName)
        _uuidFilePath = self.__loginData.inputFilename.get()
        _uuidsList = []
        # load uuids from file
        with open(_uuidFilePath) as uuidFp:
            for line in uuidFp:
                _uuidsList.append(line.rstrip("\n"))
        uuidFp.close()
        _isBackup = self.__loginData.isBackup.get()
        if _isBackup:
            _uuidsBakupList = _uuidsList
            self.__funcLib.doBackups(_uuidsBakupList, self.__batchName)
        if self.__loginData.batchEditMode == "add":
            self.__addKeywords(_uuidsList)
        elif self.__loginData.batchEditMode == "delete":
            self.__removeKeywords(_uuidsList)

try:
    removeBGDI_KeywordFromList = Remove_BGDI_Keyword_from_list()
    removeBGDI_KeywordFromList.main()                      # call the main-function 
    removeBGDI_KeywordFromList.closeLogFile()
except Exception as error:
    removeBGDI_KeywordFromList.writeLog("Error: " + str(error.args))