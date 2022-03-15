
# -*-
'''
------------------------------------------------------------------------------------------------------------------------
Autor:      Reithmeier Martin (rem) in 2022

Purpose:    This Sript add legends to the geocat MD-Records. (png and pdf)
            1. Download all needed legends to a local folder e.g. C:/downloads/legendsTemp
            1.1. In this step check: if legend have only png's -> separate it in the folder /png the others in the folder /png_pdf
            2. Add all legends as attachement to MD-Records from the local 
            3. Add all legends as onlineResources with this protocols: LEGEND:PDF | LEGEND:PNG

Remarks:    All legends are on https://github.com/geoadmin/mf-chsdi3/tree/master/chsdi/static/images/legends/
            


------------------------------------------------------------------------------------------------------------------------
'''

import sys
# sys.path.append("..\\ClassLibrary") # is needed when use outside from Visual Studio
import urllib3
from pathlib import Path
from requests.auth import HTTPBasicAuth
from geocatFunctionLib import *

mainLanguage = ""
secondLanguage = ""

# desable the exceptions of InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def checkDownloadPathExist():
    if not legendsDownloadPath.exists():
        legendsDownloadPath.mkdir(parents=True, exist_ok=True)
    elif not pngDownloadPath.exists():
        pngDownloadPath.mkdir(parents=True, exist_ok=True)
    elif not pngPdfDownloadPath.exists():
        pngPdfDownloadPath.mkdir(parents=True, exist_ok=True)

def downloads(techLayerNamesList :list):
    http = urllib3.PoolManager()

    pass

def main():
    writeLog("Script: " + batchName + " has started on environment: " + loginData.environment.get())
    global mainLanguage
    global secondLanguage
    mainLanguage, secondLanguage = setMainLanguage("ger")
    sessionCalls = API.geocatSession(loginData.urlPrefix, "eng/info?type=me", loginData.username.get(), loginData.password.get())
    requestCalls = API.geocatRequests(loginData.urlPrefix, loginData.username.get(), loginData.password.get())
    uuidAndTechLayerPairsList = getUuidAndRelatedTechLayerPairs(None, dataSource, loginData.inputFilename.get())
    checkDownloadPathExist()
    downloads(uuidAndTechLayerPairsList)
    isBackup = loginData.isBackup.get()
    if isBackup:
        uuidsBakupList = []
        # add uuids to uuidsBakupList
        doBackups(sessionCalls, uuidsBakupList, batchName)
    if loginData.batchEditMode == "add":
        addCounter = 0
        countOfMDs = str(len(uuidAndTechLayerPairsList))
        writeLog(str(addCounter) + " ???????? was added")
    elif loginData.batchEditMode == "delete":
        countOfMDs = str(len(uuidAndTechLayerPairsList))

try:
    batchName = Path(__file__).stem
    loginData = GUI.loginGUI()
    loginData.mainloop()        # open the login window

    legendsDownloadPath = Path("C:/downloads/legendsTemp")
    pngDownloadPath = Path("C:/downloads/legendsTemp/png")
    pngPdfDownloadPath = Path("C:/downloads/legendsTemp/png_pdf")

    keyword = loginData.keyword.get()
    protocol = loginData.protocol.get()
    dataSource = loginData.dataSource.get()

    logFile = openLogFile(loginData, batchName)     # open the logFile
    setLogFile(logFile)         # make logFile visible in geocatFunctionLib
    main()                      # call the function main
    logFile.close()
except Exception as error:
    writeLog("Error: " + str(error.args))   
