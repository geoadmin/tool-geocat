
from classes.gbd.corporationClasses.legislativeEntryClasses.technicalEntry import TechnicalEntry
from classes.gbd.corporationClasses.legislativeEntryClasses.executiveCorporation import ExecutiveCorporation
from classes.gbd.corporationClasses.legislativeEntryClasses.legislativeCorporation import LegislativeCorporation
from classes.gbd.corporationClasses.legislativeEntryClasses.legalBase import LegalBase
from classes.gbd.corporationClasses.legislativeEntryClasses.authority import Authority

class LegislativeEntryData():
    """legislative entry for the given corp
    Parameter:
      geocatArgs (dict):
      legiEntryData (dict):
    """

    # Attributes
    __funcLib = None
    __executiveCorporation = None
    __legislativeCorporation = None
    __catalogGroups = [] # container for all geocat groupOwner
    __executiveAuthoritiesList = [] # container for all executiveAuthority
    __legislativeAuthoritiesList = [] # container for all legislativeAuthority
    __legalBasesList = [] # container for all legalBase
    __technicalEntriesList = [] # container for all technicalEntry
    __technicalEntryResultList = []
    __geocatMdRecordsResultList = []

    def __init__(self, geocatArgs :dict, legiEntryData :dict):
        self.__technicalEntriesList.clear()
        self.__technicalEntryResultList.clear()
        self.__geocatMdRecordsResultList.clear()
        self.__geocatArgs = geocatArgs
        self.__funcLib = geocatArgs.get('funcLib')
        self.__funcLib.writeLog("[]][][]in constructor of legislativeEntryData-object")
        self.__id = legiEntryData.get('id')
        self.__labelNumber = legiEntryData.get('labelNumber')
        self.__identifier = legiEntryData.get('identifier')
        self.__delegation = legiEntryData.get('delegation')
        self.__downloadService = legiEntryData.get('downloadService')
        self.__startDate = legiEntryData.get('startDate')
        self.__endDate = legiEntryData.get('endDate')
        self.__access = legiEntryData.get('access')
        self.__oereb = legiEntryData.get('oereb')
        self.__geoReference = legiEntryData.get('geoReference')
        self.__status = legiEntryData.get('status')
        self.__isHistorised = legiEntryData.get('isHistorised')
        self.__histoData = legiEntryData.get('histoData')
        self.__isSplittable = legiEntryData.get('isSplittable')
        self.__historyReference = legiEntryData.get('historyReference')
        self.__title = legiEntryData.get('title')
        self.__titleDe = legiEntryData.get('titleDe')
        self.__titleFr = legiEntryData.get('titleFr')
        self.__titleIt = legiEntryData.get('titleIt')
        self.__titleRm = legiEntryData.get('titleRm')
        self.__delegationChoices = legiEntryData.get('delegationChoices')
        self.__customFields = legiEntryData.get('customFields')
        self.__customFieldValues = legiEntryData.get('customFieldValues')
        self.__executiveCorporation = ExecutiveCorporation(legiEntryData.get('executiveCorp'))
        self.__legislativeCorporation = LegislativeCorporation(legiEntryData.get('legislativeCorp'))
        self.__executiveAuthoritiesList = self.__loadExecutiveAuthoritiesList(legiEntryData.get('executiveAuthorities'))
        self.__legislativeAuthoritiesList = self.__loadLegislativeAuthoritiesList(legiEntryData.get('legislativeAuthorities'))
        self.__legalBasesList = self.__loadLegalBasesList(legiEntryData.get('legalBases'))
        self.__catalogGroups = geocatArgs.get('catalogGroups')
        self.__corporationId = geocatArgs.get('gbdCorpId')
        self.__geocatArgs['geocatGroupId'] = self.__getCurrentGeocatGroupId()
        self.__geocatArgs['gbdEntryId'] = self.__id
        self.__geocatArgs['gbdEntryTitle'] = self.__title
        self.__geocatArgs['corpLevel'] = self.__executiveCorporation.governmentSystemLevel
        self.__printValues()
        self.__technicalEntriesList = self.__loadTechnicalEntriesList(legiEntryData.get('technicalEntries'))
        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from constructor of legislativeEntryData-object")

    def __loadTechnicalEntriesList(self, techEntries :dict):
        _techEntriesResultList = []
        for techEntry in techEntries:
            _technicalEntryObject = TechnicalEntry(self.__geocatArgs, techEntry)
            _techEntriesResultList.append(_technicalEntryObject)
        return _techEntriesResultList

    def __loadLegalBasesList(self, legalBases :dict):
        _legalBaseResultList = []
        for lB in legalBases:
            _legalBaseResultList.append(LegalBase(lB))
        return _legalBaseResultList

    def __loadExecutiveAuthoritiesList(self, execAuthorities :dict):
        _execAuthorityResultList = []
        for execAuthority in execAuthorities:
            _execAuthorityResultList.append(Authority(execAuthority))
        return _execAuthorityResultList

    def __loadLegislativeAuthoritiesList(self, legiAuthorities :dict):
        _legiAuthorityResultList = []
        for legiAuthority in legiAuthorities:
            _legiAuthorityResultList.append(Authority(legiAuthority))
        return _legiAuthorityResultList

    def __getLegislativeEntryDataResultLine(self):
        _executiveAuthority = ""
        if self.__executiveCorporation.governmentSystemLevel == "federal" and self.delegation != "none":
            _executiveAuthority = "----"
        elif self.__executiveAuthoritiesList:
            _executiveAuthority = self.__executiveAuthoritiesList[0].nameDe
        else:
            _executiveAuthority = "----"
        resultLine = [self.__corporationId, self.id, _executiveAuthority, self.__legislativeCorporation.governmentSystemLevel, self.identifier, self.title]
#        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from legislativeEntryDataResultLine")
        return resultLine
    legislativeEntryDataResultLine = property(__getLegislativeEntryDataResultLine)

    def __getCurrentGeocatGroupId(self):
        _ownerName = ""
        if self.__legislativeCorporation.nameDe == "Bund":
            if self.__executiveAuthoritiesList:
                if self.__executiveAuthoritiesList[0].nameDe == "Generalsekretariat":
                    _ownerName = "Verteidigung, Bevölkerungsschutz und Sport"
                elif self.__executiveAuthoritiesList[0].nameDe == "Eidgenössische Forschungsanstalt für Wald, Schnee und Landschaft":
                    _ownerName = "Eidg. Forschungsanstalt für Wald, Schnee und Landschaft"
                else:
                    _ownerName = self.__executiveAuthoritiesList[0].nameDe
            else:
                _ownerName = "none"
        else:
            if self.legislativeCorp.governmentSystemLevel == "canton":
                _ownerName = "Kanton " + self.__legislativeCorporation.nameDe
            else:
                _ownerName = self.__legislativeCorporation.nameDe
        return self.__catalogGroups.getGroupOwnerId(_ownerName)

    def __printValues(self):
        authority = ""
        if self.__executiveAuthoritiesList:
            authority = self.__executiveAuthoritiesList[0].nameDe
        else:
            authority = "----"
        self.__funcLib.writeLog("[]][][]Corporation = " + self.__legislativeCorporation.nameDe + ", " + authority)
        self.__funcLib.writeLog("[]][][]entryData.corporationID = " + str(self.__legislativeCorporation.corporationID))
        self.__funcLib.writeLog("[]][][]entryData.labelNumber = " + str(self.labelNumber))
        self.__funcLib.writeLog("[]][][]entryData.identifier = " + self.identifier)
        self.__funcLib.writeLog("[]][][]entryData.delegation = " + self.delegation)
        self.__funcLib.writeLog("[]][][]entryData.title = " + self.title)
        self.__funcLib.writeLog("[]][][] | -> __loadTechnicalEntriesList()")

    def __setTechnicalEntryResultList(self):
        _technicalEntryResultList = []
        for techEntry in self.__technicalEntriesList:
            _technicalEntryResultList.append(techEntry.techEntryResultLine)
        self.__technicalEntryResultList = _technicalEntryResultList

    def getTechnicalEntryResultList(self):
        self.__setTechnicalEntryResultList()
#        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from techEntryResultList")
        return self.__technicalEntryResultList

    def __setGeocatMdRecordsResultList(self):
        _geocatMdRecordsResultList = []
        for techEntry in self.__technicalEntriesList:
            _geocatMdRecordsResultList.extend(techEntry.getGeocatMdRecordsResultList())
        self.__geocatMdRecordsResultList = _geocatMdRecordsResultList

    def getGeocatMdRecordsResultList(self):
        self.__setGeocatMdRecordsResultList()
        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from techEntrygeocatMdResultList")
        return self.__geocatMdRecordsResultList

# property sectipon ----------------------------------------------------------------------------

    def __getId(self):
        return self.__id
    id = property(__getId)

    def __getLabelNumber(self):
        return self.__labelNumber
    labelNumber = property(__getLabelNumber)

    def __getIdentifier(self):
        return self.__identifier
    identifier = property(__getIdentifier)

    def __getDelegation(self):
        return self.__delegation
    delegation = property(__getDelegation)

    def __getDownloadService(self):
        return self.__downloadService
    downloadService = property(__getDownloadService)

    def __getStartDate(self):
        return self.__startDate
    startDate = property(__getStartDate)

    def __getEndDate(self):
        return self.__endDate
    endDate = property(__getEndDate)

    def __getAccess(self):
        return self.__access
    access = property(__getAccess)

    def __getOereb(self):
        return self.__oereb
    oereb = property(__getOereb)

    def __getGeoReference(self):
        return self.__geoReference
    geoReference = property(__getGeoReference)

    def __getStatus(self):
        return self.__status
    status = property(__getStatus)

    def __getIsHistorised(self):
        return self.__isHistorised
    isHistorised = property(__getIsHistorised)

    def __getHistoData(self):
        return self.__histoData
    histoData = property(__getHistoData)

    def __getIsSplittable(self):
        return self.__isSplittable
    isSplittable = property(__getIsSplittable)

    def __getHistoryReference(self):
        return self.__historyReference
    historyReference = property(__getHistoryReference)

    def __getTitle(self):
        return self.__title
    title = property(__getTitle)

    def __getTitleDe(self):
        return self.__titleDe
    titleDe = property(__getTitleDe)

    def __getTitleFr(self):
        return self.__titleFr
    titleFr = property(__getTitleFr)

    def __getTitleIt(self):
        return self.__titleIt
    titleIt = property(__getTitleIt)

    def __getTitleRm(self):
        return self.__titleRm
    titleRm = property(__getTitleRm)

    def __getDelegationChoises(self):
        return self.__delegationChoises
    delegationChoises = property(__getDelegationChoises)

    def __getCustomFields(self):
        return self.__customFields
    customFields = property(__getCustomFields)

    def __getCustomFieldValues(self):
        return self.__customFieldValues
    customFieldValues = property(__getCustomFieldValues)
