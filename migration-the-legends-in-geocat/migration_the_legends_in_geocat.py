
# -*-
'''
------------------------------------------------------------------------------------------------------------------------
Autor:      Reithmeier Martin (rem) in 2022

Purpose:    This Sript add legends to the geocat MD-Records. (png and pdf)

Proceed:
            1. Download all needed legends to a local folder e.g. C:/downloads/legendsTemp
            1.1. In this step check: if legend have only png's -> separate it in the folder /png the others in the folder /png_pdf
            2. Add all legends as attachement to MD-Records from the local 
            3. Add all legends as onlineResources with this protocols: LEGEND:PDF | LEGEND:PNG

Remarks:    All legends are on https://github.com/geoadmin/mf-chsdi3/tree/master/chsdi/static/images/legends/
            All pdf-legends have related png-legends but not all png-legends have related pdf-legends

Important:  It is not easy to download files from a github repository. The workaround is: Download the complete repo as zip
            and extract only the legend folder to a local folder e.g. C:/downloads/legendsTemp

------------------------------------------------------------------------------------------------------------------------
'''

import sys
# sys.path.append("..\\ClassLibrary") # is needed when use outside from Visual Studio
import urllib3
import shutil
from pathlib import Path
from requests.auth import HTTPBasicAuth
from geocatFunctionLib import *

mainLanguage = ""
secondLanguage = ""

# desable the exceptions of InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def checkLocalDownloadPathExist():
    if not legendsLocalDownloadPath.exists():
        legendsLocalDownloadPath.mkdir(parents=True, exist_ok=True)
    elif not pngDownloadPath.exists():
        pngDownloadPath.mkdir(parents=True, exist_ok=True)
    elif not pngPdfDownloadPath.exists():
        pngPdfDownloadPath.mkdir(parents=True, exist_ok=True)

def getListOfUuidAndRelatedLegendFilenamePairs(uuidAndTechLayerPairsList :list):
    resultList = []
    for uuidTechlayer in uuidAndTechLayerPairsList:
        for language in const.languagesSufixList:
            legendPdfFileName = uuidTechlayer['relatedValue'] + language + "_big.pdf"
            legendPngFileName = uuidTechlayer['relatedValue'] + language + ".png"
            legendPdfFilePath = Path(legendsBasicPath + legendPdfFileName)
            legendPngFilePath = Path(legendsBasicPath + legendPngFileName)
            resultLine = {}
            resultLine['uuid'] = uuidTechlayer['uuid']
            resultLine['relatedFilename'] = uuidTechlayer['relatedValue'] + language
            if legendPdfFilePath.exists():
                resultLine['uuid'] = uuidTechlayer['uuid']
                resultLine['relatedPdfFilename'] = legendPdfFileName
                resultLine['relatedPngFilename'] = legendPngFileName
                resultList.append(resultLine)
            else:
                resultLine['uuid'] = uuidTechlayer['uuid']
                resultLine['relatedPdfFilename'] = ""
                resultLine['relatedPngFilename'] = legendPngFileName
                resultList.append(resultLine)
    return resultList

def uploadLegendFile(sessionCalls :API.geocatSession, auth :HTTPBasicAuth, urlValue :str, fileName :str, headers :dict):
    url = loginData.urlPrefix + urlValue
    if fileName.endswith(".png"):
        contentType = {'Content-Type': "image/png"}
    elif fileName.endswith(".pdf"):
        contentType = {'Content-Type': "application/pdf"}
    with open(fileName, 'rb') as uploadFile:
        files = {"file": uploadFile}
        response = requests.post(url, files=files, data=contentType, proxies=const.proxyDict, verify=False, auth=auth, headers=headers, cookies=sessionCalls.cookies)
    return response
    
def addLegendFilesToMdAsAttachment(sessionCalls :API.geocatSession, uuidAndLegendsFilename :list) -> int:
    authentication = HTTPBasicAuth(loginData.username.get(), loginData.password.get())
    countOfMDs = str(len(uuidAndLegendsFilename))
    addCounter = 0
    headers = {}
    headers['X-XSRF-TOKEN'] = sessionCalls.token
    headers['accept'] = "application/json"
    for uuid in uuidAndLegendsFilename:
        urlValue = "api/0.1/records/" + uuid['uuid'] + "/attachments?visibility=public&approved=false"

        if uuid['relatedPdfFilename']:
            legendFilenameFQN = legendsBasicPath + uuid['relatedPdfFilename']
            responsePdf = uploadLegendFile(sessionCalls, authentication, urlValue, legendFilenameFQN, headers)
            if responsePdf.status_code == 201:
                addCounter += 1
                writeLog(str(uuidAndLegendsFilename.index(uuid) + 1) + "/" + countOfMDs + ") the legend: " + uuid['relatedPdfFilename'] + " added successfully to MD: " + uuid['uuid'])
            else:
                writeLog(str(uuidAndLegendsFilename.index(uuid) + 1) + "/" + countOfMDs + ") error: " + uuid['relatedPdfFilename'] + " not added to MD: " + uuid['uuid'])
        legendFilenameFQN = legendsBasicPath + uuid['relatedPngFilename']
        responsePng = uploadLegendFile(sessionCalls, authentication, urlValue, legendFilenameFQN, headers)
        if responsePng.status_code == 201:
            addCounter += 1
            writeLog(str(uuidAndLegendsFilename.index(uuid) + 1) + "/" + countOfMDs + ") the legend: " + uuid['relatedPngFilename'] + " added successfully to MD: " + uuid['uuid'])
        else:
            writeLog(str(uuidAndLegendsFilename.index(uuid) + 1) + "/" + countOfMDs + ") error: " + uuid['relatedPngFilename'] + " not added to MD: " + uuid['uuid'])
    return addCounter

def deleteLegendFilesFromMDs(sessionCalls :API.geocatSession, uuidAndTechLayerPairsList):
    authentication = HTTPBasicAuth(loginData.username.get(), loginData.password.get())
    countOfMDs = str(len(uuidAndTechLayerPairsList))
    headers = {}
    headers['X-XSRF-TOKEN'] = sessionCalls.token
    headers['accept'] = "application/json"
    for uuid in uuidAndTechLayerPairsList:
        urlValue = "api/0.1/records/" + uuid['uuid'] + "/attachments?visibility=public&approved=false"
        url = loginData.urlPrefix + urlValue
        response = requests.delete(url, proxies=const.proxyDict, verify=False, auth=authentication, headers=headers, cookies=sessionCalls.cookies)
        writeLog(str(uuidAndTechLayerPairsList.index(uuid) + 1) + "/" + countOfMDs + ") all legends: from MD: " + uuid['uuid'] + " are deleted")
        writeLog("Status Code: " + str(response.status_code) + "")

def getOnLineNodeParameters(legendType :str, uuid :str, techLayerName :str)  -> dict:
    if legendType == "PNG":
        ext = "." + legendType.lower()
    elif legendType == "PDF":
        ext = "_big." + legendType.lower()

    onLineNodeParameters = {}
    onLineNodeParameters['urlValueDe'] = loginData.urlPrefix + "api/0.1/records/" + uuid + "/attachments/" + techLayerName + "_de" + ext
    onLineNodeParameters['urlValueFr'] = loginData.urlPrefix + "api/0.1/records/" + uuid + "/attachments/" + techLayerName + "_fr" + ext
    onLineNodeParameters['urlValueIt'] = loginData.urlPrefix + "api/0.1/records/" + uuid + "/attachments/" + techLayerName + "_it" + ext
    onLineNodeParameters['urlValueEn'] = loginData.urlPrefix + "api/0.1/records/" + uuid + "/attachments/" + techLayerName + "_en" + ext
    onLineNodeParameters['urlValueRm'] = loginData.urlPrefix + "api/0.1/records/" + uuid + "/attachments/" + techLayerName + "_rm" + ext
    onLineNodeParameters['resourceNameValueDe'] = "Legende (" + legendType + ")"
    onLineNodeParameters['resourceNameValueFr'] = "Légende (" + legendType + ")"
    onLineNodeParameters['resourceNameValueIt'] = "Legenda (" + legendType + ")"
    onLineNodeParameters['resourceNameValueEn'] = "Legend (" + legendType + ")"
    onLineNodeParameters['resourceNameValueRm'] = "Legenda (" + legendType + ")"
    onLineNodeParameters['protocol'] = "LEGEND:" + legendType
    onLineNodeParameters['function'] = "information"
    return onLineNodeParameters

def updatingRecords(sessionCalls :API.geocatSession, uuidAndTechLayerPairsList, uuidAndLegendFilenamePairsList):
    addCounter = 0
    countOfMDs = str(len(uuidAndTechLayerPairsList))
    for uuidAndTechLayerPairs in uuidAndTechLayerPairsList:
        muiIndex = uuidAndTechLayerPairsList.index(uuidAndTechLayerPairs) * 5
        if uuidAndLegendFilenamePairsList[muiIndex]['relatedPdfFilename']:
            onLineNodeParameters = getOnLineNodeParameters("PDF", uuidAndTechLayerPairs['uuid'], uuidAndTechLayerPairs['relatedValue'])
            writeLog(str(uuidAndTechLayerPairsList.index(uuidAndTechLayerPairs) + 1) + "/" + countOfMDs + ") add xml-Node >onLine< to MD: " + uuidAndTechLayerPairs['uuid'])
            addCounter += addXmlOnLineNode(sessionCalls, uuidAndTechLayerPairs, onLineNodeParameters)
        onLineNodeParameters = getOnLineNodeParameters("PNG", uuidAndTechLayerPairs['uuid'], uuidAndTechLayerPairs['relatedValue'])
        writeLog(str(uuidAndTechLayerPairsList.index(uuidAndTechLayerPairs) + 1) + "/" + countOfMDs + ") add xml-Node >onLine< to MD: " + uuidAndTechLayerPairs['uuid'])
        addCounter += addXmlOnLineNode(sessionCalls, uuidAndTechLayerPairs, onLineNodeParameters)
    return str(addCounter)

def main():
    writeLog("Script: " + batchName + " has started on environment: " + loginData.environment.get())
    global mainLanguage
    global secondLanguage
    mainLanguage, secondLanguage = setMainLanguage("ger")
    sessionCalls = API.geocatSession(loginData.urlPrefix, "eng/info?type=me", loginData.username.get(), loginData.password.get())
    requestCalls = API.geocatRequests(loginData.urlPrefix, loginData.username.get(), loginData.password.get())
    uuidAndTechLayerPairsList = getUuidAndRelatedTechLayerPairs(None, dataSource, loginData.inputFilename.get())
    if loginData.batchEditMode == "add":
        uuidAndLegendFilenamePairsList = getListOfUuidAndRelatedLegendFilenamePairs(uuidAndTechLayerPairsList)
        isBackup = loginData.isBackup.get()
        if isBackup:
            uuidsBakupList = []
            for uuid in uuidAndTechLayerPairsList:
                uuidsBakupList.append(uuid['uuid'])
            doBackups(sessionCalls, uuidsBakupList, batchName)
        addCounter = addLegendFilesToMdAsAttachment(sessionCalls, uuidAndLegendFilenamePairsList)
        writeLog(str(addCounter) + " legend-files was added")
        updatedRecords = updatingRecords(sessionCalls, uuidAndTechLayerPairsList, uuidAndLegendFilenamePairsList)
        writeLog("total " + updatedRecords + " online resources was added")

    elif loginData.batchEditMode == "delete":
        deleteAttachments = True
        deleteOnlineResources = True
        if deleteAttachments:
            deleteLegendFilesFromMDs(sessionCalls, uuidAndTechLayerPairsList)
            countOfMDs = str(len(uuidAndTechLayerPairsList))
            writeLog("all legend-files deleted from " + countOfMDs + " MDs")
        if deleteOnlineResources:
            xmlElementPng = getResponseAsXmlTree(requestCalls, "&protocol=LEGEND:PNG", mainLanguage)
            if xmlElementPng:
                uuidsListPng = xmlElementPng.findall(".//uuid")
                deleteOnlineResourceWithGivenProtocol(sessionCalls, "LEGEND:PNG", uuidsList=uuidsListPng, uuid="")
            xmlElementPdf = getResponseAsXmlTree(requestCalls, "&protocol=LEGEND:PDF", mainLanguage)
            if xmlElementPdf:
                uuidsListPdf = xmlElementPdf.findall(".//uuid")
                deleteOnlineResourceWithGivenProtocol(sessionCalls, "LEGEND:PDF", uuidsList=uuidsListPdf, uuid="")


try:
    batchName = Path(__file__).stem
    loginData = GUI.loginGUI()
    loginData.mainloop()        # open the login window

    legendsLocalDownloadPath = Path("C:/downloads/legendsTemp")
    legendsBasicPath = "C:/downloads/legendsTemp/legends/"

    keyword = loginData.keyword.get()
    protocol = loginData.protocol.get()
    dataSource = loginData.dataSource.get()

    logFile = openLogFile(loginData, batchName)     # open the logFile
    setLogFile(logFile)         # make logFile visible in geocatFunctionLib
    main()                      # call the function main
    logFile.close()
except Exception as error:
    writeLog("Error: " + str(error.args))   
