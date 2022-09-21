"""

"""

import sys
# sys.path.append("..\\ClassLibrary") # is needed when use outside from Visual Studio
import urllib3
import pandas as panelData
from pathlib import Path
import datetime as TimeStamp
import geocatLoginGUI as GUI
import geocatApiCalls as API
import geocatGroups as groupOwners
import geocatLoginGUI as GUI
import geocatConstants as const
import geocatFunctionLib as funcLib

from classes.geoBasicData import GeoBasicData

# desable the exceptions of InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CheckMdRecordExistForBasicGeoData():

    # Attributes
    __funcLib = funcLib.FunctionLibrary()
    __loginData = GUI.LoginGUI()
    __batchName = Path(__file__).stem
    __sessionCalls = None
    __requestCalls = None
    __catalogGroups = None
    __geoBasicData = None

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

    def __writeDataToCsv(self, gbdCatalog :GeoBasicData):
        _corpList = gbdCatalog.getCorpResultList()
        _entryDataList = gbdCatalog.getEntryDataResultList()
        _techEntryList = gbdCatalog.getTechEntryResultList()
        _gcMDsList = gbdCatalog.getGcMdsResultList()
        _corpColumns = ['corpID', 'Gemeinwesen', 'Kürzel']
        _entryDataColumns = ['corpID', 'entryID', 'Zuständige Stelle', 'Gemeinwesen Level', 'Gemeinwesen ID', 'Bezeichnung']
        _techEntryColumns = ['entryID', 'techEntryID', 'Tech. Datensatz Label', 'Tech. Datensatz Bezeichnung']
        _gcMDsColumns = ['techEntryID', 'gcTitel', 'gcGemeinsamerTitel', 'gcBasicGeodataId', 'gcBasicGeodataType', 'gcPermaLink', 'gcAusdehnung']
        _corpDataFrame = panelData.DataFrame(data=_corpList, columns=_corpColumns)
        _entryDataFrame = panelData.DataFrame(data=_entryDataList, columns=_entryDataColumns)
        _techEntryDataFrame = panelData.DataFrame(data=_techEntryList, columns=_techEntryColumns)
        _gcMDsDataFrame = panelData.DataFrame(data=_gcMDsList, columns=_gcMDsColumns)
        _joinedDataFrame = panelData.merge(panelData.merge(panelData.merge(_corpDataFrame, _entryDataFrame, how='outer', on='corpID'), _techEntryDataFrame, how='outer', on='entryID'), _gcMDsDataFrame, how='outer', on='techEntryID')
        _joinedDataFrame.to_csv(Path('./' + TimeStamp.datetime.now().strftime("%Y-%m-%d-%H%M") + 'allCorpsResult.csv'), sep=';', na_rep='na', index=False, encoding='utf-8')

    def main(self):
        """  """
        self.__funcLib.writeLog("Script: " + self.__batchName + " has started on environment: " + self.__loginData.environment.get())
        self.__sessionCalls = API.GeocatSession(self.__loginData.urlPrefix, "eng/info?type=me", self.__loginData.username.get(), self.__loginData.password.get())
        self.__requestCalls = API.GeocatRequests(self.__loginData.urlPrefix, self.__loginData.username.get(), self.__loginData.password.get())
        self.__funcLib.setApiCalls(self.__sessionCalls, self.__requestCalls)
        self.__catalogGroups = groupOwners.GeocatGroups(self.__loginData.urlPrefix, self.__loginData.username.get(), self.__loginData.password.get())
        _geocatArgs = {'catalogGroups': self.__catalogGroups, 'funcLib': self.__funcLib}
        _corporationName = "Bund"
        self.__geoBasicData = GeoBasicData(_geocatArgs, _corporationName)
        self.__writeDataToCsv(self.__geoBasicData)

try:
    checkMdRecordExistForBasicGeoData = CheckMdRecordExistForBasicGeoData()     # create the renameProtocolValue-object
    checkMdRecordExistForBasicGeoData.main()                      # call the main-function 
    checkMdRecordExistForBasicGeoData.closeLogFile()
except Exception as error:
    checkMdRecordExistForBasicGeoData.writeLog("Error: " + str(error.args))