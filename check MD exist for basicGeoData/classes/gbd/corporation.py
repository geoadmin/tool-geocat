
import requests
import geocatConstants as const
from classes.gbd.corp import Corp
from classes.gbd.corporationClasses.legislativeEntryData import LegislativeEntryData

class Corporation(Corp):
    """ Corporation (inherited from Corp) inclusive a List with all legislative entries. I
    Include a list of all legislative entries for the given corporation. For each legislative entry, the linked technical entries are also returned. 
    \tThis list only returns published or archived entries but no drafts.
    
    Parameter:
    ----------
    :geocatArgs: [dict] Arguments, which need to now in other classes
    :corp: [dict] Data from the given corporation
    
    Attribute:
    """

    # Attributes
    __funcLib = None
    __legislitiveEntriesList = [] # container for all legislativeEntryData
    __entryDataResultList = []
    __technicalEntryResultList = []
    __geocatMdRecordsResultList = []

    def __init__(self, geocatArgs :dict, corp :dict):
        super().__init__(corp)
        self.__legislitiveEntriesList.clear()
        self.__entryDataResultList.clear()
        self.__technicalEntryResultList.clear()
        self.__geocatMdRecordsResultList.clear()
        self.__funcLib = geocatArgs.get('funcLib')
        self.__funcLib.writeLog("[]]in constructor of corporationItem-object")
        geocatArgs["gbdCorpId"] = self.corporationID 
        self.__geocatArgs = geocatArgs
        self.__legislitiveEntriesList = self.__loadLegislativeEntries()
        #self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from constructor of corporationItem-object")

    def __loadLegislativeEntries(self):
        """  """
        _legiEntryResultList = []
        self.__funcLib.writeLog("[]][]load all the entryData-objects from geobasisdaten.ch for this corporationID = " + str(self.corporationID))
        _response = requests.request('GET', 'https://geobasisdaten.ch/api/v1/data/?legislative_corp=' + str(self.corporationID) + '&format=json', proxies=const.proxyDict)
        _legiEntriesDataResponseList = _response.json()
        for legiEntryData in _legiEntriesDataResponseList:
            _legiEntryDataObject = LegislativeEntryData(self.__geocatArgs, legiEntryData)
            _legiEntryResultList.append(_legiEntryDataObject)
#            if _legiEntriesDataResponseList.index(legiEntryData) > 5:
#                return _legiEntryResultList
        return _legiEntryResultList


    def __getCorpResultLine(self):
 #       self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from corporationResultLine")
        return [self.corporationID, self.corporationName, self.abbreviation]
    corporationResultLine = property(__getCorpResultLine)

    def __setEntryDataResultList(self):
        """  """
        _entryDataResultList = []
        for legiEntry in self.__legislitiveEntriesList:
            _entryDataResultList.append(legiEntry.legislativeEntryDataResultLine)
        self.__entryDataResultList = _entryDataResultList

    def getEntryDataResultList(self):
        """  """
        self.__setEntryDataResultList()
#        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from legislativeEntryDataResultList")
        return self.__entryDataResultList

    def __setTechEntryResultList(self):
        """  """
        _techEntryResultList = []
        for legiEntry in self.__legislitiveEntriesList:
            _techEntryResultList.extend(legiEntry.getTechnicalEntryResultList())
        self.__technicalEntryResultList = _techEntryResultList

    def getTechEntryResultList(self):
        """  """
        self.__setTechEntryResultList()
#        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from legiEntrytechEntryResultList")
        return self.__technicalEntryResultList

    def __setGcMdsResultList(self):
        """  """
        _gcMdsResultList = []
        for legiEntry in self.__legislitiveEntriesList:
            _gcMdsResultList.extend(legiEntry.getGeocatMdRecordsResultList())
        self.__geocatMdRecordsResultList = _gcMdsResultList

    def getGcMdsResultList(self):
        """  """
        self.__setGcMdsResultList()
        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from legiEntrytechEntrygeocatMdResultList")
        return self.__geocatMdRecordsResultList

