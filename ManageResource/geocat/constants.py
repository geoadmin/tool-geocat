NS = {
    'csw': 'http://www.opengis.net/cat/csw/2.0.2',
    'gco': 'http://www.isotc211.org/2005/gco',
    'che': 'http://www.geocat.ch/2008/che',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'srv': 'http://www.isotc211.org/2005/srv',
    'gmx': 'http://www.isotc211.org/2005/gmx',
    'gts': 'http://www.isotc211.org/2005/gts',
    'gsr': 'http://www.isotc211.org/2005/gsr',
    'gmi': 'http://www.isotc211.org/2005/gmi',
    'gml': 'http://www.opengis.net/gml/3.2',
    'xlink': 'http://www.w3.org/1999/xlink',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'geonet': 'http://www.fao.org/geonetwork',
    'java': 'java:org.fao.geonet.util.XslUtil',
}

ENV = {
    'int': 'https://geocat-int.dev.bgdi.ch',
    'prod': 'https://www.geocat.ch',
}

PROXY = [
    {
        "http": "proxy-bvcol.admin.ch:8080",
        "https": "proxy-bvcol.admin.ch:8080",
    },
    {
        "http": "proxy.admin.ch:8080",
        "https": "proxy.admin.ch:8080",
    },
    {}
]

LANG_ISO = {
    "ger": "DE",
    "fre": "FR",
    "ita": "IT",
    "eng": "EN",
    "roh": "RM"
}

XML_TAG = {
    "distributionInfo": "<gmd:distributionInfo xmlns:java='java:org.fao.geonet.util.XslUtil' xmlns:gmd='http://www.isotc211.org/2005/gmd'>" \
                        "<gmd:MD_Distribution></gmd:MD_Distribution>" \
                    "</gmd:distributionInfo>",
    "transferOptions": "<gmd:transferOptions xmlns:gmd='http://www.isotc211.org/2005/gmd'>" \
                        "<gmd:MD_DigitalTransferOptions></gmd:MD_DigitalTransferOptions>" \
                    "</gmd:transferOptions>",
    "onLine_layer": "<gmd:onLine xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:che='http://www.geocat.ch/2008/che' xmlns:gco='http://www.isotc211.org/2005/gco' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>" \
                "<gmd:CI_OnlineResource>" \
                    "<gmd:linkage xsi:type='che:PT_FreeURL_PropertyType'>"\
                        "<che:PT_FreeURL></che:PT_FreeURL>" \
                    "</gmd:linkage>"\
                    "<gmd:protocol>"\
                        "<gco:CharacterString></gco:CharacterString>"\
                    "</gmd:protocol>" \
                    "<gmd:name xsi:type='gmd:PT_FreeText_PropertyType'>" \
                        "<gmd:PT_FreeText></gmd:PT_FreeText>" \
                    "</gmd:name>" \
                    "<gmd:description xsi:type='gmd:PT_FreeText_PropertyType'>" \
                        "<gmd:PT_FreeText></gmd:PT_FreeText>" \
                    "</gmd:description>" \
                "</gmd:CI_OnlineResource>" \
            "</gmd:onLine>",
    "onLine_service": "<gmd:onLine xmlns:gmd='http://www.isotc211.org/2005/gmd' xmlns:che='http://www.geocat.ch/2008/che' xmlns:gco='http://www.isotc211.org/2005/gco' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>" \
                "<gmd:CI_OnlineResource>" \
                    "<gmd:linkage xsi:type='che:PT_FreeURL_PropertyType'>"\
                        "<che:PT_FreeURL></che:PT_FreeURL>" \
                    "</gmd:linkage>"\
                    "<gmd:protocol>"\
                        "<gco:CharacterString></gco:CharacterString>"\
                    "</gmd:protocol>" \
                "</gmd:CI_OnlineResource>" \
            "</gmd:onLine>"
}