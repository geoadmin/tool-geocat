
import geocatConstants as const

class GeocatMD():
    """description of class
    Parameter:
    ----------
    :techEntryId:
    :uuid:
    :metaData:

    Attribute:
    ----------
    :_techEntryId:
    :_uuid:
    :_permaLink:
    :_titel:
    :_basicGeodataId:
    :_basicGeodataType:
    :_extentDescriptionList:
    
    Property:
    ----------
    <gmd:collectiveTitle>
        <gco:CharacterString>
    """

    # Attributes
    __funcLib = None

    def __init__(self, techEntryId, uuid, mdRecord, funcLib):
        self.__funcLib = funcLib
        self.__funcLib.writeLog("[]][][][][][][]in constructor of geocatMD-object")
        self.__techEntryId = techEntryId
        self.__uuid = uuid
        self.__permaLink = "https://www.geocat.ch/geonetwork/srv/ger/catalog.search#/metadata/" + uuid
        self.__titel = ""
        self.__gcCollectiveTitle = ""
        self.__basicGeodataId = ""
        self.__basicGeodataType = ""
        self.__extentDescriptionList = []
        self.__setPropertyValues(mdRecord)
        self.__printValues()
        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from constructor of geocatMD-object")

    def __setPropertyValues(self, metaData):
        """ get the information from the md-record (metaData) to set the corresponding property values """
        _identificationAsRoot = metaData.find(".//gmd:identificationInfo", const.ns)
        if _identificationAsRoot:
            self.__gcCollectiveTitle = _identificationAsRoot.find(".//gmd:collectiveTitle/gco:CharacterString", const.ns).text
            _CHE_MD_dataIdentificationAsRoot = _identificationAsRoot.find(".//che:CHE_MD_DataIdentification", const.ns)
            _MD_DataIdentificationAsRoot = _identificationAsRoot.find(".//gmd:MD_DataIdentification", const.ns)
            if _CHE_MD_dataIdentificationAsRoot or _MD_DataIdentificationAsRoot:
                if _CHE_MD_dataIdentificationAsRoot:
                    _CI_CitationAsRoot = _CHE_MD_dataIdentificationAsRoot.find(".//gmd:CI_Citation", const.ns)
                    self.__titel = _CI_CitationAsRoot.find(".//gmd:title/gco:CharacterString", const.ns).text
                    _basicGeodataIdAsRoot = _CHE_MD_dataIdentificationAsRoot.find(".//che:basicGeodataID", const.ns)
                    if _basicGeodataIdAsRoot:
                        self.__basicGeodataId = _basicGeodataIdAsRoot.find(".//gco:CharacterString", const.ns).text
                    _basicGeodataIdTypeAsRoot = _CHE_MD_dataIdentificationAsRoot.find(".//che:basicGeodataIDType", const.ns)
                    if _basicGeodataIdTypeAsRoot:
                        _basicGeodataIDTypeCode = _basicGeodataIdTypeAsRoot.find(".//che:basicGeodataIDTypeCode", const.ns)
                        self.__basicGeodataType = _basicGeodataIDTypeCode.attrib['codeListValue']
                if _MD_DataIdentificationAsRoot:
                    _CHE_MD_dataIdentificationAsRoot = _MD_DataIdentificationAsRoot
                _extentDescriptionList = _CHE_MD_dataIdentificationAsRoot.findall(".//gmd:extent/gmd:EX_Extent/gmd:description/gco:CharacterString", const.ns)
                for extentDescription in _extentDescriptionList:
                    if extentDescription.text:
                        self.__extentDescriptionList.append(extentDescription.text)

    def __printValues(self):
        self.__funcLib.writeLog("[]][][][][][][]geocatMD.permaLink = https://www.geocat.ch/geonetwork/srv/ger/catalog.search#/metadata/" + self.__uuid)
        self.__funcLib.writeLog("[]][][][][][][]geocatMD.titel = " + self.__titel)
        self.__funcLib.writeLog("[]][][][][][][]geocatMD.collectiveTitle = " + self.__gcCollectiveTitle)
        if self.__basicGeodataId:
            self.__funcLib.writeLog("[]][][][][][][]geocatMD.basicGeodataId = " + self.__basicGeodataId)
        else:
            self.__funcLib.writeLog("[]][][][][][][]geocatMD.basicGeodataId = -> None")
        self.__funcLib.writeLog("[]][][][][][][]geocatMD.basicGeodataType = " + self.__basicGeodataType)
        for extentDescription in self.__extentDescriptionList:
            self.__funcLib.writeLog("[]][][][][][][]geocatMD.extentDescription = " + extentDescription)

    def __getResultLine(self):
        """ return the md information as list which corresponding the search condition
        ['techEntryID', 'gcTitel', 'gcBasicGeodataId', 'gcBasicGeodataType', 'gcPermaLink', 'gcExtentDescription']
        """
        _mdResultLine = []
        _extDescription = ""
        if self.__basicGeodataId:
            _mdResultLine = [self.__techEntryId, self.__titel, self.__gcCollectiveTitle, self.__basicGeodataId, self.__basicGeodataType, self.__permaLink]
        else:
            _mdResultLine = [self.__techEntryId, self.__titel, self.__gcCollectiveTitle, 'None', self.__basicGeodataType, self.__permaLink]
        for extText in self.__extentDescriptionList:
            _extDescription += extText + ", "
        _mdResultLine.append(_extDescription)
        self.__funcLib.writeLog("<<<<<<<<<<<<<<<<< return from geocatMdResultLine")
        return _mdResultLine
    mdRecordResultLine = property(__getResultLine)

