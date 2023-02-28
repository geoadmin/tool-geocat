from lxml import etree as ET
import geopycat
import settings
import json
from urllib.parse import unquote


def add_status_obsolete(metadata: bytes) -> list:
    """
    Returns list of edits for the batch editing API request to add the status oboslete
    """

    body = []
    root = ET.fromstring(metadata)

    if len(root.xpath(".//gmd:identificationInfo//gmd:status/gmd:MD_ProgressCode",
            namespaces=geopycat.settings.NS)) > 0:

        body.append(
            {
                "xpath": "./gmd:identificationInfo//gmd:status/gmd:MD_ProgressCode/parent::*",
                "value": "<gn_delete></gn_delete>"
            }
        )

    body.append(
        {
            "xpath": "./gmd:identificationInfo[1]/*",
            "value": f"<gn_add>{settings.XML['status_obsolete']}</gn_add>"
        }
    )

    return body

def remove_status_obsolete(metadata: bytes) -> list:
    """
    Returns list of edits for the batch editing API request to remove the status oboslete
    """

    body = []
    root = ET.fromstring(metadata)
    tree = ET.ElementTree(root)

    for i in root.xpath(".//gmd:identificationInfo//gmd:status/gmd:MD_ProgressCode[@codeListValue='obsolete']",
                        namespaces=geopycat.settings.NS):

        body.append(
            {
                "xpath": tree.getpath(i.getparent()),
                "value": "<gn_delete></gn_delete>"
            }
        )

    return body

def add_bgdi_keyword(metadata: bytes) -> list:
    """
    Returns list of edits for the batch editing API request to add the BGDI Keyword.
    """

    body = []
    root = ET.fromstring(metadata)
    tree = ET.ElementTree(root)

    # If a descriptiveKeywords section with geocat thesaurus exists, replace it with additional keyword
    if len(root.xpath("./gmd:identificationInfo//gmd:descriptiveKeywords[contains(@xlink:href, 'thesaurus=local.theme.geocat.ch')]",
            namespaces=geopycat.settings.NS)) > 0:

        tag = root.xpath("./gmd:identificationInfo//gmd:descriptiveKeywords[contains(@xlink:href, 'thesaurus=local.theme.geocat.ch')]",
                    namespaces=geopycat.settings.NS)[0]

        xlink = unquote(tag.attrib["{http://www.w3.org/1999/xlink}href"])
        ids = xlink.split("?")[-1].split("id=")[-1].split("&")[0] + "," + settings.BGDI_KW_ID

        body.append(
            {
                "xpath": tree.getpath(tag),
                "value": "<gn_delete></gn_delete>"
            }
        )

        body.append(
            {
                "xpath": "./gmd:identificationInfo[1]/*",
                "value": f"<gn_add>{settings.XML['keyword'].replace('keyword_id', ids)}</gn_add>"
            }
        )

    # If not, create new descriptiveKeywords section
    else:

        body.append(
            {
                "xpath": "./gmd:identificationInfo[1]/*",
                "value": f"<gn_add>{settings.XML['keyword'].replace('keyword_id', settings.BGDI_KW_ID)}</gn_add>"
            }
        )

    return body

def remove_bgdi_keyword(metadata: bytes) -> list:
    """
    Returns list of edits for the batch editing API request to remove the BGDI Keyword.
    """

    body = []
    root = ET.fromstring(metadata)

    # Delete all descriptiveKeywords that have only one keyword = BGDI
    xpath = "./gmd:identificationInfo//gmd:descriptiveKeywords[(.//gmd:keyword/gco:CharacterString = 'BGDI Bundesgeodaten-Infrastruktur' or .//gmd:keyword/gmd:PT_FreeText//gmd:LocalisedCharacterString = 'BGDI Bundesgeodaten-Infrastruktur') and count(.//gmd:keyword)=1]"
    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:
        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    # Delete all gmd:keyword = BGDI in descriptiveKeywords that have more than one keyword
    xpath = "./gmd:identificationInfo//gmd:descriptiveKeywords[count(.//gmd:keyword)>1]//gmd:keyword[./gco:CharacterString = 'BGDI Bundesgeodaten-Infrastruktur' or ./gmd:PT_FreeText//gmd:LocalisedCharacterString = 'BGDI Bundesgeodaten-Infrastruktur']"
    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:
        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    # Get all keyword id of descriptiveKeywords with xlink:href containing BGDI keyword id
    # Delete all descriptiveKeywords with xlink:href containing BGDI keyword id
    # Add one descriptiveKeywords with all ids
    xpath = f"./gmd:identificationInfo//gmd:descriptiveKeywords[contains(@xlink:href, '{settings.BGDI_KW_ID}')]"
    all_ids = list()
    for i in root.xpath(xpath, namespaces=geopycat.settings.NS):

        xlink = unquote(i.attrib["{http://www.w3.org/1999/xlink}href"])
        ids = xlink.split("?")[-1].split("id=")[-1].split("&")[0].split(",")
        all_ids += ids

    all_ids = [i for i in all_ids if i != settings.BGDI_KW_ID]

    if len(all_ids) > 0:
        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

        body.append({
            "xpath": "./gmd:identificationInfo[1]/*",
            "value": f"<gn_add>{settings.XML['keyword'].replace('keyword_id', ','.join(all_ids))}</gn_add>"
        })

    return body

def add_identifier(metadata: bytes, identifier: str) -> list:
    """
    Returns list of edits for the batch editing API request to add an identifier.
    """

    body = []
    root = ET.fromstring(metadata)

    # If an identifier exists, erase it before adding a new one
    xpath = "./gmd:identificationInfo//gmd:citation//gmd:identifier"
    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    body.append({
        "xpath": "./gmd:identificationInfo[1]/*/gmd:citation[1]/gmd:CI_Citation",
        "value": f"<gn_add>{settings.XML['identifier'].replace('layer_id', identifier)}</gn_add>"
    })

    return body

def add_wms(metadata: bytes, layer_id: str, layer_title: dict) -> list:
    """
    Returns list of edits for the batch editing API request to add WMS resource.
    """

    body = []
    root = ET.fromstring(metadata)

    url = "https://wms.geo.admin.ch/?SERVICE=WMS&amp;VERSION=1.3.0&amp;REQUEST=GetCapabilities"

    value = settings.XML["resource"].replace("resource-url-de", url).replace("resource-url-fr", url).replace("resource-url-it", url).replace("resource-url-en", url).replace("resource-url-rm", url)
    value = value.replace("resource-protocol", "OGC:WMS")
    value = value.replace("resource-name-de", layer_id).replace("resource-name-fr", layer_id).replace("resource-name-it", layer_id).replace("resource-name-en", layer_id).replace("resource-name-rm", layer_id)
    value = value.replace("resource-desc-de", layer_title["de"])
    value = value.replace("resource-desc-fr", layer_title["fr"])
    value = value.replace("resource-desc-it", layer_title["it"])
    value = value.replace("resource-desc-en", layer_title["en"])
    value = value.replace("resource-desc-rm", layer_title["de"])

    # If no distribution section, we don't add WMS
    if len(root.xpath("./gmd:distributionInfo", namespaces=geopycat.settings.NS)) == 0:
        return body

    # No transferOption
    if len(root.xpath("./gmd:distributionInfo//gmd:transferOptions", 
                        namespaces=geopycat.settings.NS)) == 0:

        body.append({
            "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution",
            "value": f"<gn_add>{settings.XML['transferOption']}</gn_add>"
        })

        body.append({
            "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions",
            "value": f"<gn_add>{value}</gn_add>"
        })

        return body   

    # transferOption with only one child and WMS
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)=1"\
            " and .//gmd:protocol/gco:CharacterString = 'OGC:WMS'"\
            " and (.//gmd:URL[contains(text(), 'wms.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'wms.geo.admin.ch')])]"

    number_tags = len(root.xpath("./gmd:distributionInfo//gmd:transferOptions",
                    namespaces=geopycat.settings.NS))

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

        if number_tags == len(root.xpath(xpath, namespaces=geopycat.settings.NS)):

            body.append({
                "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution",
                "value": f"<gn_add>{settings.XML['transferOption']}</gn_add>"
            })

            body.append({
                "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions",
                "value": f"<gn_add>{value}</gn_add>"
            })

            return body

    # transferOption with multiple childs
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)>1]//gmd:onLine["\
            " .//gmd:protocol/gco:CharacterString = 'OGC:WMS'"\
            " and (.//gmd:URL[contains(text(), 'wms.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'wms.geo.admin.ch')])]"

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    body.append({
        "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions[1]/gmd:MD_DigitalTransferOptions",
        "value": f"<gn_add>{value}</gn_add>"
    })

    return body

def remove_wms(metadata: bytes) -> list:
    """
    Returns list of edits for the batch editing API request to remove WMS resource.
    """

    body = []
    root = ET.fromstring(metadata)

    # transferOption with only one child and WMS
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)=1"\
            " and .//gmd:protocol/gco:CharacterString = 'OGC:WMS'"\
            " and (.//gmd:URL[contains(text(), 'wms.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'wms.geo.admin.ch')])]"

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    # transferOption with multiple childs
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)>1]//gmd:onLine["\
            " .//gmd:protocol/gco:CharacterString = 'OGC:WMS'"\
            " and (.//gmd:URL[contains(text(), 'wms.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'wms.geo.admin.ch')])]"

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    return body

def add_wmts(metadata: bytes, layer_id: str, layer_title: dict) -> list:
    """
    Returns list of edits for the batch editing API request to add WMTS resource.
    """

    body = []
    root = ET.fromstring(metadata)

    url = "https://wmts.geo.admin.ch/EPSG/21781/1.0.0/WMTSCapabilities.xml"

    value = settings.XML["resource"].replace("resource-url-de", url).replace("resource-url-fr", url).replace("resource-url-it", url).replace("resource-url-en", url).replace("resource-url-rm", url)
    value = value.replace("resource-protocol", "OGC:WMTS")
    value = value.replace("resource-name-de", layer_id).replace("resource-name-fr", layer_id).replace("resource-name-it", layer_id).replace("resource-name-en", layer_id).replace("resource-name-rm", layer_id)
    value = value.replace("resource-desc-de", layer_title["de"])
    value = value.replace("resource-desc-fr", layer_title["fr"])
    value = value.replace("resource-desc-it", layer_title["it"])
    value = value.replace("resource-desc-en", layer_title["en"])
    value = value.replace("resource-desc-rm", layer_title["de"])

    # If no distribution section, we don't add WMTS
    if len(root.xpath("./gmd:distributionInfo", namespaces=geopycat.settings.NS)) == 0:
        return body

    # No transferOption
    if len(root.xpath("./gmd:distributionInfo//gmd:transferOptions", 
                        namespaces=geopycat.settings.NS)) == 0:

        body.append({
            "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution",
            "value": f"<gn_add>{settings.XML['transferOption']}</gn_add>"
        })

        body.append({
            "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions",
            "value": f"<gn_add>{value}</gn_add>"
        })

        return body   

    # transferOption with only one child and WMTS
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)=1"\
            " and .//gmd:protocol/gco:CharacterString = 'OGC:WMTS'"\
            " and (.//gmd:URL[contains(text(), 'wmts.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'wmts.geo.admin.ch')])]"

    number_tags = len(root.xpath("./gmd:distributionInfo//gmd:transferOptions",
                    namespaces=geopycat.settings.NS))

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

        if number_tags == len(root.xpath(xpath, namespaces=geopycat.settings.NS)):

            body.append({
                "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution",
                "value": f"<gn_add>{settings.XML['transferOption']}</gn_add>"
            })

            body.append({
                "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions",
                "value": f"<gn_add>{value}</gn_add>"
            })

            return body

    # transferOption with multiple childs
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)>1]//gmd:onLine["\
            " .//gmd:protocol/gco:CharacterString = 'OGC:WMTS'"\
            " and (.//gmd:URL[contains(text(), 'wmts.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'wmts.geo.admin.ch')])]"

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    body.append({
        "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions[1]/gmd:MD_DigitalTransferOptions",
        "value": f"<gn_add>{value}</gn_add>"
    })

    return body

def remove_wmts(metadata: bytes) -> list:
    """
    Returns list of edits for the batch editing API request to remove WMTS resource.
    """

    body = []
    root = ET.fromstring(metadata)

    # transferOption with only one child and WMTS
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)=1"\
            " and .//gmd:protocol/gco:CharacterString = 'OGC:WMTS'"\
            " and (.//gmd:URL[contains(text(), 'wmts.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'wmts.geo.admin.ch')])]"

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    # transferOption with multiple childs
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)>1]//gmd:onLine["\
            " .//gmd:protocol/gco:CharacterString = 'OGC:WMTS'"\
            " and (.//gmd:URL[contains(text(), 'wmts.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'wmts.geo.admin.ch')])]"

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    return body

def add_api3(metadata: bytes, layer_id: str) -> list:
    """
    Returns list of edits for the batch editing API request to add API3 resource.
    """

    body = []
    root = ET.fromstring(metadata)

    url =  f"{settings.API3_URL}/{layer_id}"

    value = settings.XML["resource"].replace("resource-url-de", url).replace("resource-url-fr", url).replace("resource-url-it", url).replace("resource-url-en", url).replace("resource-url-rm", url)
    value = value.replace("resource-protocol", "ESRI:REST")
    value = value.replace("resource-name-de", "RESTful API von geo.admin.ch")
    value = value.replace("resource-name-fr", "RESTful API de geo.admin.ch")
    value = value.replace("resource-name-it", "RESTful API da geo.admin.ch")
    value = value.replace("resource-name-en", "RESTful API from geo.admin.ch")
    value = value.replace("resource-name-rm", "RESTful API dad geo.admin.ch")
    value = value[:value.index("<gmd:description")] + value[value.index("</gmd:description>")+len("</gmd:description>"):]


    # If no distribution section, we don't add API3
    if len(root.xpath("./gmd:distributionInfo", namespaces=geopycat.settings.NS)) == 0:
        return body

    # No transferOption
    if len(root.xpath("./gmd:distributionInfo//gmd:transferOptions", 
                        namespaces=geopycat.settings.NS)) == 0:

        body.append({
            "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution",
            "value": f"<gn_add>{settings.XML['transferOption']}</gn_add>"
        })

        body.append({
            "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions",
            "value": f"<gn_add>{value}</gn_add>"
        })

        return body   

    # transferOption with only one child and API3
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)=1"\
            " and .//gmd:protocol/gco:CharacterString = 'ESRI:REST'"\
            " and (.//gmd:URL[contains(text(), 'api3.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'api3.geo.admin.ch')])]"

    number_tags = len(root.xpath("./gmd:distributionInfo//gmd:transferOptions",
                    namespaces=geopycat.settings.NS))

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

        if number_tags == len(root.xpath(xpath, namespaces=geopycat.settings.NS)):

            body.append({
                "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution",
                "value": f"<gn_add>{settings.XML['transferOption']}</gn_add>"
            })

            body.append({
                "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions",
                "value": f"<gn_add>{value}</gn_add>"
            })

            return body

    # transferOption with multiple childs
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)>1]//gmd:onLine["\
            " .//gmd:protocol/gco:CharacterString = 'ESRI:REST'"\
            " and (.//gmd:URL[contains(text(), 'api3.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'api3.geo.admin.ch')])]"

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    body.append({
        "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions[1]/gmd:MD_DigitalTransferOptions",
        "value": f"<gn_add>{value}</gn_add>"
    })

    return body

def remove_api3(metadata: bytes) -> list:
    """
    Returns list of edits for the batch editing API request to remove API3 resource.
    """

    body = []
    root = ET.fromstring(metadata)

    # transferOption with only one child and API3
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)=1"\
            " and .//gmd:protocol/gco:CharacterString = 'ESRI:REST'"\
            " and (.//gmd:URL[contains(text(), 'api3.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'api3.geo.admin.ch')])]"

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    # transferOption with multiple childs
    xpath = "./gmd:distributionInfo//gmd:transferOptions[count(./*/*)>1]//gmd:onLine["\
            " .//gmd:protocol/gco:CharacterString = 'ESRI:REST'"\
            " and (.//gmd:URL[contains(text(), 'api3.geo.admin.ch')]"\
            " or .//che:LocalisedURL[contains(text(), 'api3.geo.admin.ch')])]"

    if len(root.xpath(xpath, namespaces=geopycat.settings.NS)) > 0:

        body.append({
            "xpath": xpath,
            "value": "<gn_delete></gn_delete>"
        })

    return body

def add_mappreview(metadata: bytes, layer_id: str) -> list:
    """
    Returns list of edits for the batch editing API request to add map preview resource.
    """

    body = []
    root = ET.fromstring(metadata)

    url = f"https://map.geo.admin.ch/?layers={layer_id}"

    value = settings.XML["resource"].replace("resource-url-de", url).replace("resource-url-fr", url).replace("resource-url-it", url).replace("resource-url-en", url).replace("resource-url-rm", url)
    value = value.replace("resource-protocol", "MAP:Preview")
    value = value.replace("resource-name-de", "Vorschau map.geo.admin.ch")
    value = value.replace("resource-name-fr", "Aperçu map.geo.admin.ch")
    value = value.replace("resource-name-it", "Previsione map.geo.admin.ch")
    value = value.replace("resource-name-en", "Preview map.geo.admin.ch")
    value = value.replace("resource-name-rm", "Vorschau map.geo.admin.ch")
    value = value[:value.index("<gmd:description")] + value[value.index("</gmd:description>")+len("</gmd:description>"):]


    # If no distribution section, we don't add map preview
    if len(root.xpath("./gmd:distributionInfo", namespaces=geopycat.settings.NS)) == 0:
        return body

    # No transferOption
    if len(root.xpath("./gmd:distributionInfo//gmd:transferOptions", 
                        namespaces=geopycat.settings.NS)) == 0:

        body.append({
            "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution",
            "value": f"<gn_add>{settings.XML['transferOption']}</gn_add>"
        })

        body.append({
            "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions",
            "value": f"<gn_add>{value}</gn_add>"
        })

        return body

    body.append({
        "xpath": "./gmd:distributionInfo[1]/gmd:MD_Distribution/gmd:transferOptions[1]/gmd:MD_DigitalTransferOptions",
        "value": f"<gn_add>{value}</gn_add>"
    })

    return body


# TESTING
geocat = geopycat.geocat(env='prod')
md = geocat.get_metadata_from_mef(uuid="5d8ccc02-21c5-4757-b723-588f6a09fffe")
layer_id = "ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill"
layer_title = {
    "de": "Layer title de",
    "fr": "Layer title fr",
    "it": "Layer title it",
    "en": "Layer title en"
}
# print(json.dumps(add_wms(md, layer_id, layer_title)))
# print(json.dumps(add_wmts(md, layer_id, layer_title)))
# print(json.dumps(remove_wmts(md)))
# print(json.dumps(add_api3(md, layer_id)))
# print(json.dumps(remove_api3(md)))
print(json.dumps(add_mappreview(md, layer_id)))