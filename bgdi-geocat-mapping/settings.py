GD_SPREADSHEET_ID = "1to10g8bIhVv0GxMQZk00Yc-kIk9FpMzQJp6veFXgN6s"
GD_SHEET_NAME = "Planning%20overview"

GD_SHEET = f"https://docs.google.com/spreadsheets/d/{GD_SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={GD_SHEET_NAME}"

BGDI_GROUP_ID = [
    "69", "51", "53", "25", "41", "52", "40", "27", "37", "39", "38", "8", "34", "6",
    "23", "26", "22", "29125806", "26805108", "13", "36", "50", "19647867"
    ]

WMS_URL = "https://wms.geo.admin.ch/?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities"

WMTS_URL = "https://wmts.geo.admin.ch/EPSG/4326/1.0.0/WMTSCapabilities.xml"

API3_URL = "https://api3.geo.admin.ch/rest/services/api/MapServer"

NS = {
    "wms": "http://www.opengis.net/wms",
    "wmts": "http://www.opengis.net/wmts/1.0",
    "ows": "http://www.opengis.net/ows/1.1"
}

XML = {
    "status_obsolete": "<gmd:status xmlns:gmd='http://www.isotc211.org/2005/gmd'>" \
                            "<gmd:MD_ProgressCode codeList='http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/codelist/ML_gmxCodelists.xml#MD_ProgressCode' codeListValue='obsolete'/>" \
                        "</gmd:status>",
    "keyword": "<gmd:descriptiveKeywords xmlns:gmd='http://www.isotc211.org/2005/gmd' "\
                    "xmlns:xlink='http://www.w3.org/1999/xlink' " \
                    "xlink:href='local://srv/api/registries/vocabularies/keyword?" \
                    "skipdescriptivekeywords=true&amp;thesaurus=local.theme.geocat.ch&amp;" \
                    "id=keyword_id&amp;lang=ger,fre,ita,eng,roh'></gmd:descriptiveKeywords>",
    "identifier": "<gmd:identifier xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:gco='http://www.isotc211.org/2005/gco'>" \
                    "<gmd:MD_Identifier>" \
                        "<gmd:code>" \
                            "<gco:CharacterString>layer_id</gco:CharacterString>" \
                        "</gmd:code>" \
                    "</gmd:MD_Identifier>" \
                "</gmd:identifier>",
    "resource": "<gmd:onLine xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:che='http://www.geocat.ch/2008/che' xmlns:gco='http://www.isotc211.org/2005/gco'>"\
                "<gmd:CI_OnlineResource>"\
                    "<gmd:linkage xsi:type='che:PT_FreeURL_PropertyType'>"\
                        "<che:PT_FreeURL>"\
                           "<che:URLGroup>"\
                              "<che:LocalisedURL locale='#DE'>resource-url-de</che:LocalisedURL>"\
                           "</che:URLGroup>"\
                           "<che:URLGroup>"\
                              "<che:LocalisedURL locale='#FR'>resource-url-fr</che:LocalisedURL>"\
                           "</che:URLGroup>"\
                           "<che:URLGroup>"\
                              "<che:LocalisedURL locale='#IT'>resource-url-it</che:LocalisedURL>"\
                           "</che:URLGroup>"\
                           "<che:URLGroup>"\
                              "<che:LocalisedURL locale='#EN'>resource-url-en</che:LocalisedURL>"\
                           "</che:URLGroup>"\
                           "<che:URLGroup>"\
                              "<che:LocalisedURL locale='#RM'>resource-url-rm</che:LocalisedURL>"\
                           "</che:URLGroup>"\
                        "</che:PT_FreeURL>"\
                    "</gmd:linkage>"\
                    "<gmd:protocol>"\
                        "<gco:CharacterString>resource-protocol</gco:CharacterString>"\
                    "</gmd:protocol>"\
                    "<gmd:name xsi:type='gmd:PT_FreeText_PropertyType'>"\
                        "<gmd:PT_FreeText>"\
                           "<gmd:textGroup>"\
                              "<gmd:LocalisedCharacterString locale='#DE'>resource-name-de</gmd:LocalisedCharacterString>"\
                           "</gmd:textGroup>"\
                           "<gmd:textGroup>"\
                              "<gmd:LocalisedCharacterString locale='#FR'>resource-name-fr</gmd:LocalisedCharacterString>"\
                           "</gmd:textGroup>"\
                           "<gmd:textGroup>"\
                              "<gmd:LocalisedCharacterString locale='#IT'>resource-name-it</gmd:LocalisedCharacterString>"\
                           "</gmd:textGroup>"\
                           "<gmd:textGroup>"\
                              "<gmd:LocalisedCharacterString locale='#EN'>resource-name-en</gmd:LocalisedCharacterString>"\
                           "</gmd:textGroup>"\
                           "<gmd:textGroup>"\
                              "<gmd:LocalisedCharacterString locale='#RM'>resource-name-rm</gmd:LocalisedCharacterString>"\
                           "</gmd:textGroup>"\
                        "</gmd:PT_FreeText>"\
                    "</gmd:name>"\
                    "<gmd:description xsi:type='gmd:PT_FreeText_PropertyType'>"\
                        "<gmd:PT_FreeText>"\
                           "<gmd:textGroup>"\
                              "<gmd:LocalisedCharacterString locale='#DE'>resource-desc-de</gmd:LocalisedCharacterString>"\
                           "</gmd:textGroup>"\
                           "<gmd:textGroup>"\
                              "<gmd:LocalisedCharacterString locale='#FR'>resource-desc-fr</gmd:LocalisedCharacterString>"\
                           "</gmd:textGroup>"\
                           "<gmd:textGroup>"\
                              "<gmd:LocalisedCharacterString locale='#IT'>resource-desc-it</gmd:LocalisedCharacterString>"\
                           "</gmd:textGroup>"\
                           "<gmd:textGroup>"\
                              "<gmd:LocalisedCharacterString locale='#EN'>resource-desc-en</gmd:LocalisedCharacterString>"\
                           "</gmd:textGroup>"\
                           "<gmd:textGroup>"\
                              "<gmd:LocalisedCharacterString locale='#RM'>resource-desc-rm</gmd:LocalisedCharacterString>"\
                           "</gmd:textGroup>"\
                        "</gmd:PT_FreeText>"\
                    "</gmd:description>"\
                "</gmd:CI_OnlineResource>"\
            "</gmd:onLine>",
    "transferOption": "<gmd:transferOptions xmlns:gmd='http://www.isotc211.org/2005/gmd'>"\
                        "<gmd:MD_DigitalTransferOptions>"\
                        "</gmd:MD_DigitalTransferOptions>"\
                    "</gmd:transferOptions>"
}

BGDI_KW_ID = [
   "http%3A%2F%2Fcustom.shared.obj.ch%2Fconcept%23ae677a16-f81a-4533-9243-a87831115079",
   "http://custom.shared.obj.ch/concept#ae677a16-f81a-4533-9243-a87831115079"
]