
"""

"""

import requests
import geocatConstants as const
from classes.gbd.corporation import Corporation

class GeoBasicData():
    """ This class is the entrypoint for the geo-basic-data catalog 
    Parameter:
    ----------
    :geocatArgs: [dict]
    :corpName: [str]

    Attribute:
    ----------
    :_catalog: [Corporations]
    :_catalogByName: [Corporations]
        
    """

    # Attributes
    __funcLib = None
    __geoBasicDataCorporationsList = []
    __corporationsResultList = []
    __entryDataResultList = []
    __technicalEntryResultList = []
    __geocatMdRecordsResultList = []

    def __init__(self, geocatArgs :dict, corporationName :str):
        self.__geoBasicDataCorporationsList.clear()
        self.__funcLib = geocatArgs.get('funcLib')
        self.__funcLib.writeLog("-> in constructor of geoBasicData-object")
        self.__geocatArgs = geocatArgs
        self.__geoBasicDataCorporationsList = self.__loadCorporationsList(corporationName)
        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from constructor of geoBasicData-object")

    def __loadCorporationsList(self, corporationName=""):
        """  """
        _corporationsDataList = []
        self.__funcLib.writeLog("->[load all corporations from geobasisdaten.ch")
        _response = requests.request('GET', 'https://geobasisdaten.ch/api/v1/corp/?format=json', proxies=const.proxyDict)
        _corporationsResponseList = _response.json()
        if not corporationName:
            for corp in _corporationsResponseList:
                _corporationsDataList.append(Corporation(self.__geocatArgs, corp))
            return _corporationsDataList
        else:
            for corp in _corporationsResponseList:
                if corp['nameDe'] == corporationName:
                    _corporationObject = Corporation(self.__geocatArgs, corp)
                    _corporationsDataList.append(_corporationObject)
                return _corporationsDataList

    def __setCorpResultList(self):
        _corporationsResultList = []
        for corp in self.__geoBasicDataCorporationsList:
            _corporationsResultList.append(corp.corporationResultLine)
        self.__corporationsResultList = _corporationsResultList

    def getCorpResultList(self):
        self.__setCorpResultList()
#        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from corporationResultList")
        return self.__corporationsResultList

    def __setEntryDataResultList(self):
        """  """
        _entryDataResultList = []
        for corp in self.__geoBasicDataCorporationsList:
            _entryDataResultList.extend(corp.getEntryDataResultList())
        self.__entryDataResultList = _entryDataResultList

    def getEntryDataResultList(self):
        """  """
        self.__setEntryDataResultList()
#        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from corplegislativeEntryDataResultList")
        return self.__entryDataResultList

    def __setTechEntryResultList(self):
        """  """
        _techEntryResultList = []
        for corp in self.__geoBasicDataCorporationsList:
            _techEntryResultList.extend(corp.getTechEntryResultList())
        self.__technicalEntryResultList = _techEntryResultList

    def getTechEntryResultList(self):
        """  """
        self.__setTechEntryResultList()
 #       self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from corplegiEntrytechEntryResultList")
        return self.__technicalEntryResultList

    def __setGcMdsResultList(self):
        """  """
        _geocatMdRecordsResultList = []
        for corp in self.__geoBasicDataCorporationsList:
            _geocatMdRecordsResultList.extend(corp.getGcMdsResultList())
        self.__geocatMdRecordsResultList = _geocatMdRecordsResultList

    def getGcMdsResultList(self):
        """  """
        self.__setGcMdsResultList()
        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from corplegiEntrytechEntrygeocatMdResultList")
        return self.__geocatMdRecordsResultList
