import sys
# sys.path.append("..\\ClassLibrary") # is needed when use outside from Visual Studio
import requests
import urllib3
from pathlib import Path
from requests.auth import HTTPBasicAuth
from geocatFunctionLib import *

mainLanguage = ""
secondLanguage = ""

# desable the exceptions of InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def checkThesaurusLink(sessionCalls :API.geocatSession, uuidsList):
    for uuid in uuidsList:
        print("MD Nr: ", uuidsList.index(uuid) + 1)
        metaData = ElementTree.fromstring(getMdRecordAsXml(sessionCalls, uuid.text))
        if metaData.tag != 'apiError':
            descriptiveKeywordAsRoot = metaData.find(".//gmd:descriptiveKeywords", const.ns)
            if descriptiveKeywordAsRoot:
                try:
                    anchors = descriptiveKeywordAsRoot.findall(".//gmx:Anchor", const.ns)
                    link = anchors[0].attrib['{http://www.w3.org/1999/xlink}href']
                    if "geocat-int.dev.bgdi.ch" in link:
                        writeLog("uuid= " + uuid.text + ", link= " + link)
                except Exception as error:
                    writeLog("Error: " + str(error.args))

def main():
    """ logical main sequence """
    writeLog("Script: " + batchName + " has started on environment: " + loginData.environment.get())
    global mainLanguage
    global secondLanguage
    mainLanguage, secondLanguage = setMainLanguage("ger")
    sessionCalls = API.geocatSession(loginData.urlPrefix, "eng/info?type=me", loginData.username.get(), loginData.password.get())
    requestCalls = API.geocatRequests(loginData.urlPrefix, loginData.username.get(), loginData.password.get())
    geocatUuidsList1 = getResponseAsXmlTree(requestCalls, const.isNotHarvested, mainLanguage).findall(".//uuid")
    checkThesaurusLink(sessionCalls, geocatUuidsList1)
    geocatUuidsList2 = getResponseAsXmlTree(requestCalls, const.isNotHarvested, mainLanguage, start="1501", end="3000").findall(".//uuid")
    checkThesaurusLink(sessionCalls, geocatUuidsList2)
    geocatUuidsList3 = getResponseAsXmlTree(requestCalls, const.isNotHarvested, mainLanguage, start="3001", end="4500").findall(".//uuid")
    checkThesaurusLink(sessionCalls, geocatUuidsList3)
    geocatUuidsList4 = getResponseAsXmlTree(requestCalls, const.isNotHarvested, mainLanguage, start="4501", end="6000").findall(".//uuid")
    checkThesaurusLink(sessionCalls, geocatUuidsList4)
    geocatUuidsList5 = getResponseAsXmlTree(requestCalls, const.isNotHarvested, mainLanguage, start="6001", end="7500").findall(".//uuid")
    checkThesaurusLink(sessionCalls, geocatUuidsList5)
    pass

try:
    batchName = Path(__file__).stem
    loginData = GUI.loginGUI()
    loginData.mainloop()        # open the login window

    keyword = loginData.keyword.get()
    protocol = loginData.protocol.get()

    logFile = openLogFile(loginData, batchName)     # open the logFile
    setLogFile(logFile)         # make logFile visible in geocatFunctionLib
    main()                      # call the function main
    logFile.close()
except Exception as error:
    writeLog("Error: " + str(error.args))   
