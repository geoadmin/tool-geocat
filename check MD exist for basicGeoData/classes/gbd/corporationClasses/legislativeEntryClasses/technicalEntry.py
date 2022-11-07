

import xml.etree.ElementTree as ElementTree
import geocatConstants as const
from classes.gbd.corporationClasses.legislativeEntryClasses.geoCategory import GeoCategory
from classes.geocat.geocatMD import GeocatMD


class TechnicalEntry():
    """TechnicalEntryData
    Parameter:
      geocatArgs:
      technicalEntry:
      
    """

    # Attributes
    __funcLib = None
    __geoCategory = None
    __geocatMdRecordsList = [] # container for all geocatMD
    __geocatMdRecordsResultList = []

    def __init__(self, geocatArgs :dict, technicalEntry :dict):
        self.__geocatMdRecordsList.clear()
        self.__geocatMdRecordsResultList.clear()
        self.__geocatArgs = geocatArgs
        self.__funcLib = geocatArgs.get('funcLib')
        #self.__funcLib.writeLog("[]][][][][]in constructor of technicalEntry-object")
        self.__id = technicalEntry.get('id')
        self.__label = technicalEntry.get('label')
        self.__labelNumber = technicalEntry.get('labelNumber')
        self.__startDate = technicalEntry.get('startDate')
        self.__endDate = technicalEntry.get('endDate')
        self.__metadataUrls = technicalEntry.get('metadataUrls')
        self.__status = technicalEntry.get('status')
        self.__isHistorised = technicalEntry.get('isHistorised')
        self.__hideLabel = technicalEntry.get('hideLabel')
        self.__description = technicalEntry.get('description')
        self.__descriptionDe = technicalEntry.get('descriptionDe')
        self.__descriptionFr = technicalEntry.get('descriptionFr')
        self.__descriptionIt = technicalEntry.get('descriptionIt')
        self.__descriptionRm = technicalEntry.get('descriptionRm')
        self.__dataModelUrl = technicalEntry.get('dataModelUrl')
        self.__dataModelUrlDe = technicalEntry.get('dataModelUrlDe')
        self.__dataModelUrlFr = technicalEntry.get('dataModelUrlFr')
        self.__dataModelUrlIt = technicalEntry.get('dataModelUrlIt')
        self.__dataModelUrlRm = technicalEntry.get('dataModelUrlRm')
        self.__dataModelChanges = technicalEntry.get('dataModelChanges')
        self.__dataModelChangesDe = technicalEntry.get('dataModelChangesDe')
        self.__dataModelChangesFr = technicalEntry.get('dataModelChangesFr')
        self.__dataModelChangesIt = technicalEntry.get('dataModelChangesIt')
        self.__dataModelChangesRm = technicalEntry.get('dataModelChangesRm')
        self.__modelDocumentationUrl = technicalEntry.get('modelDocumentationUrl')
        self.__modelDocumentationUrlDe = technicalEntry.get('modelDocumentationUrlDe')
        self.__modelDocumentationUrlFr = technicalEntry.get('modelDocumentationUrlFr')
        self.__modelDocumentationUrlIt = technicalEntry.get('modelDocumentationUrlIt')
        self.__modelDocumentationUrlRm = technicalEntry.get('modelDocumentationUrlRm')
        self.__dataModelUrlLabel = technicalEntry.get('dataModelUrlLabel')
        self.__dataModelUrlLabelDe = technicalEntry.get('dataModelUrlLabelDe')
        self.__dataModelUrlLabelFr = technicalEntry.get('dataModelUrlLabelFr')
        self.__dataModelUrlLabelIt = technicalEntry.get('dataModelUrlLabelIt')
        self.__dataModelUrlLabelRm = technicalEntry.get('dataModelUrlLabelRm')
        self.__modelDocumentationUrlLabel = technicalEntry.get('modelDocumentationUrlLabel')
        self.__modelDocumentationUrlLabelDe = technicalEntry.get('modelDocumentationUrlLabelDe')
        self.__modelDocumentationUrlLabelFr = technicalEntry.get('modelDocumentationUrlLabelFr')
        self.__modelDocumentationUrlLabelIt = technicalEntry.get('modelDocumentationUrlLabelIt')
        self.__modelDocumentationUrlLabelRm = technicalEntry.get('modelDocumentationUrlLabelRm')
        self.__geoCategory = self.__getGeoCategory(technicalEntry.get('geoCategory'))
        self.__geocatGroupId = geocatArgs.get('geocatGroupId')
        self.__gbdEntryTitle = geocatArgs.get('gbdEntryTitle')
        self.__corpLevel = geocatArgs.get('corpLevel')
        self.__gbdEntryId =  geocatArgs.get('gbdEntryId')
        self.__printValues()
        self.__geocatMdRecordsList = self.__loadGeocatMdRecordsList()
        #self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from constructor of technicalEntry-object")


    def __loadGeocatMdRecordsList(self):
        def _getSearchValue(any, gcGroupId):
            if any:
                return "&any=" + any + "&facet.q=groupOwner%2F" + gcGroupId + "%26isPublishedToAll%2Fy%26type%2Fbasicgeodata"
            else:
                return "&facet.q=groupOwner%2F" + gcGroupId + "%26isPublishedToAll%2Fy%26type%2Fbasicgeodata"

        def _getCountOfMDs(respons):
            return respons.find("./summary").attrib["count"]

        _geocatMdRecordsResultList = []
        if self.__geocatGroupId != -1:
            _any = ""
            _any = self.__description
            if not _any:
                _any = self.__gbdEntryTitle
            #if _any.find('&') != -1:
            #    _any = _any.replace("&", "%26")
            _searchValue = _getSearchValue(_any, str(self.__geocatGroupId))
            _searchRespons = self.__funcLib.getResponseAsXmlTree(_searchValue, "ger")
            _countOfMDs = _getCountOfMDs(_searchRespons)
            if _countOfMDs == '0':
                _any = ""
                _searchValue = _getSearchValue(_any, str(self.__geocatGroupId))
                _searchRespons = self.__funcLib.getResponseAsXmlTree(_searchValue, "ger")
                _countOfMDs = _getCountOfMDs(_searchRespons)
            _geocatUuidsList = list(_searchRespons.findall(".//uuid"))
            for uuid in _geocatUuidsList:
                _index = str(_geocatUuidsList.index(uuid)) + "/"
                _responseContent = self.__funcLib.getMdRecordAsXml(uuid.text).decode("utf-8")
                while not _responseContent.startswith("<?xml"):
                    _responseContent = self.__funcLib.getMdRecordAsXml(uuid.text).decode("utf-8")
                _geocatMdRecordAsElement = ElementTree.fromstring(_responseContent)
                _identificationAsRoot = _geocatMdRecordAsElement.find(".//gmd:identificationInfo", const.ns)
                if _identificationAsRoot:
                    _gcCollectiveTitleObject = _identificationAsRoot.find(".//gmd:collectiveTitle/gco:CharacterString", const.ns)
                    if _gcCollectiveTitleObject != None:
                        _gcCollectiveTitle = _gcCollectiveTitleObject.text
                        self.__funcLib.writeLog("[]][][][][] " + _index + _countOfMDs + "/" + self.__label + " check if gcCollectiveTitle and gbdEntryTitle are equal")
                        if _gcCollectiveTitle == self.__gbdEntryTitle:
                            _geocatMdObject = GeocatMD(self.__id, uuid.text, _geocatMdRecordAsElement, self.__funcLib)
                            _geocatMdRecordsResultList.append(_geocatMdObject)
                            self.__funcLib.writeLog("[]][][][][][][] gcCollectiveTitle and gbdEntryTitle was equal")
                            self.__funcLib.writeLog("-----------------------------------------------------------------")
        return _geocatMdRecordsResultList

    def __getTechnicalEntryResultLine(self):
        """ return this techEntry information as list 
        ['entryID', 'techEntryID', 'techEntryLabel', 'techEntryDescription']
        """
#        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from techEntryResultLine")
        return [self.__gbdEntryId, self.__id, self.__label, self.__description]
    techEntryResultLine = property(__getTechnicalEntryResultLine)

    def __getGeoCategory(self, gCategory :dict):
        """  """
        if gCategory:
            return GeoCategory(gCategory)
        else:
            return gCategory

    def __printValues(self):
        self.__funcLib.writeLog("[]][][][][]techEntry.label = " + self.__label)
        self.__funcLib.writeLog("[]][][][][]techEntry.description = " + self.__description)
        self.__funcLib.writeLog("[]][][][][]entryData.titel = " + self.__gbdEntryTitle)
        self.__funcLib.writeLog("[]][][][][] | -> __loadGeocatMdRecordsList()")

    def __setGeocatMdRecordsResultList(self):
        _geocatMdRecordsResultList = []
        for geocatMdRecord in self.__geocatMdRecordsList:
            _geocatMdRecordsResultList.append(geocatMdRecord.mdRecordResultLine)
        self.__geocatMdRecordsResultList = _geocatMdRecordsResultList

    def getGeocatMdRecordsResultList(self):
        self.__setGeocatMdRecordsResultList()
        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from geocatMdResultList")
        return self.__geocatMdRecordsResultList

# property sectipon ----------------------------------------------------------------------------

    def __getId(self):
        return self.__id
    id = property(__getId)

    def __getLabel(self):
        return self.__label
    label = property(__getLabel)

    def __getLabelNumber(self):
        return self.__labelNumber
    labelNumber = property(__getLabelNumber)

    def __getStartDate(self):
        return self.__startDate
    startDate = property(__getStartDate)

    def __getEndDate(self):
        return self.__endDate
    endDate = property(__getEndDate)

    def __getMetadataUrls(self):
        return self.__metadataUrls
    metadataUrls = property(__getMetadataUrls)

    def __getStatus(self):
        return self.__status
    status = property(__getStatus)

    def __getIsHistorised(self):
        return self.__isHistorised
    isHistorised = property(__getIsHistorised)

    def __getHideLabel(self):
        return self.__hideLabel
    hideLabel = property(__getHideLabel)

    def __getDescription(self):
        return self.__description
    description = property(__getDescription)

    def __getDescriptionDe(self):
        return self.__descriptionDe
    descriptionDe = property(__getDescriptionDe)

    def __getDescriptionFr(self):
        return self.__descriptionFr
    descriptionFr = property(__getDescriptionFr)

    def __getDescriptionIt(self):
        return self.__descriptionIt
    descriptionIt = property(__getDescriptionIt)

    def __getDescriptionRm(self):
        return self.__descriptionRm
    descriptionRm = property(__getDescriptionRm)

    def __getDataModelUrl(self):
        return self.__dataModelUrl
    dataModelUrl = property(__getDataModelUrl)

    def __getDataModelUrlDe(self):
        return self.__dataModelUrlDe
    dataModelUrlDe = property(__getDataModelUrlDe)

    def __getDataModelUrlFr(self):
        return self.__dataModelUrlFr
    dataModelUrlFr = property(__getDataModelUrlFr)

    def __getDataModelUrlIt(self):
        return self.__dataModelUrlIt
    dataModelUrlIt = property(__getDataModelUrlIt)

    def __getDataModelUrlRm(self):
        return self.__dataModelUrlRm
    dataModelUrlRm = property(__getDataModelUrlRm)

    def __getDataModelChanges(self):
        return self.__dataModelChanges
    dataModelChanges = property(__getDataModelChanges)

    def __getDataModelChangesDe(self):
        return self.__dataModelChangesDe
    dataModelChangesDe = property(__getDataModelChangesDe)

    def __getDataModelChangesFr(self):
        return self.__dataModelChangesFr
    dataModelChangesFr = property(__getDataModelChangesFr)

    def __getDataModelChangesIt(self):
        return self.__dataModelChangesIt
    dataModelChangesIt = property(__getDataModelChangesIt)

    def __getDataModelChangesRm(self):
        return self.__dataModelChangesRm
    dataModelChangesRm = property(__getDataModelChangesRm)

    def __getModelDocumentationUrl(self):
        return self.__modelDocumentationUrl
    modelDocumentationUrl = property(__getModelDocumentationUrl)

    def __getModelDocumentationUrlDe(self):
        return self.__modelDocumentationUrlDe
    modelDocumentationUrlDe = property(__getModelDocumentationUrlDe)

    def __getModelDocumentationUrlFr(self):
        return self.__modelDocumentationUrlFr
    modelDocumentationUrlFr = property(__getModelDocumentationUrlFr)

    def __getModelDocumentationUrlIt(self):
        return self.__modelDocumentationUrlIt
    modelDocumentationUrlIt = property(__getModelDocumentationUrlIt)

    def __getModelDocumentationUrlRm(self):
        return self.__modelDocumentationUrlRm
    modelDocumentationUrlRm = property(__getModelDocumentationUrlRm)

    def __getModelDocumentationUrlLabel(self):
        return self.__modelDocumentationUrlLabel
    modelDocumentationUrlLabel = property(__getModelDocumentationUrlLabel)

    def __getModelDocumentationUrlLabelDe(self):
        return self.__modelDocumentationUrlLabelDe
    modelDocumentationUrlLabelDe = property(__getModelDocumentationUrlLabelDe)

    def __getModelDocumentationUrlLabelFr(self):
        return self.__modelDocumentationUrlLabelFr
    modelDocumentationUrlLabelFr = property(__getModelDocumentationUrlLabelFr)

    def __getModelDocumentationUrlLabelIt(self):
        return self.__modelDocumentationUrlLabelIt
    modelDocumentationUrlLabelIt = property(__getModelDocumentationUrlLabelIt)

    def __getModelDocumentationUrlLabelRm(self):
        return self.__modelDocumentationUrlLabelRm
    modelDocumentationUrlLabelDe = property(__getModelDocumentationUrlLabelRm)

