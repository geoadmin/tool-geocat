from geocat import GeocatAPI, NS
import xml.etree.ElementTree as ET
import requests
import json

UUID = "429526a5-bd16-4059-8f46-7af310761e4a"

geocat = GeocatAPI()


def get_getcapabilities_url(UUID):
    response = geocat.getMDbyUUID(UUID)
    xmlroot = ET.fromstring(response.text)

    getcap_url = []
    for i in xmlroot.findall('.//{' + NS['che'] + '}LocalisedURL'):
        if type(i.text) == str:
            if "REQUEST=GetCapabilities" in i.text:
                if i.text not in getcap_url:
                    getcap_url.append(i.text)

    if len(getcap_url) > 1:
        print("More the one GetCapabilities URL found, choose the one you want\n")
        print(getcap_url)
        index = int(input(f'Choose from 0 to {len(getcap_url) - 1} : '))
        return getcap_url[index]
    else:
        return getcap_url[0]


def get_layername_geocatid(getcap_url, metadata_service_url):
    response = requests.get(url=getcap_url, proxies=geocat.proxies)
    xmlroot = ET.fromstring(response.text)
    namespace = xmlroot.tag.split('}')[0] + '}'

    geoservice_layers = []

    for layer in xmlroot.findall('.//' + namespace + 'Layer'):
        if len(layer.findall(namespace + 'Name')) > 1:
            print("Layer has more than one name, by default take the first one !")

        geoservice_layers.append(layer.findall(namespace + 'Name')[0].text)

    response = requests.get(url=metadata_service_url, proxies=geocat.proxies)
    response = json.loads(response.text)

    layername_geocatid = []

    for service_layer in geoservice_layers:
        for api_layer in response["layers"]:
            if service_layer == api_layer["layerBodId"]:
                layername_geocatid.append({"LayerName": service_layer, "GeoCatID" : api_layer["idGeoCat"]})
                break
    print(f"Layers in geoserive: {len(geoservice_layers)}")
    print(f"Layers in metadata service matching the geoservice: {len(layername_geocatid)}")
    return layername_geocatid


def add_coupled_resources(UUID, resources, number):
    count = 0.0
    for i in range(number - 1):
        # xpath logic : when adding new element at the end of existing ones or when there is no existing ones,
        # give the parent element. Geocat knows where to put the new element
        # When you want to add a new element among a list of already existing elements, you can specify where to insert it :
        # In the Xpath, go down to the element you want to add and specify the position [1,2,3,...],
        # it will be added just before the specified one. To select the last one, add the position [last()]
        xpath_coupled = "/che:CHE_MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification"
        value_coupled = f"<srv:coupledResource xmlns:srv='{NS['srv']}' xmlns:gco='{NS['gco']}' >\
        <srv:SV_CoupledResource>\
        <srv:operationName>\
        <gco:CharacterString>GetCapabilities</gco:CharacterString>\
        </srv:operationName>\
        <srv:identifier>\
        <gco:CharacterString>{resources[i]['GeoCatID']}</gco:CharacterString>\
        </srv:identifier>\
        <gco:ScopedName>{resources[i]['LayerName']}</gco:ScopedName>\
        </srv:SV_CoupledResource>\
        </srv:coupledResource>"

        xpath_operates = "/che:CHE_MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification"
        value_operates = f'<srv:operatesOn xmlns:srv="{NS["srv"]}" xmlns:xlink="{NS["xlink"]}" uuidref="{resources[i]["GeoCatID"]}" xlink:href="https://geocat-int.dev.bgdi.ch/geonetwork/srv/fre/csw?service=CSW&amp;request=GetRecordById&amp;version=2.0.2&amp;outputSchema=http://www.isotc211.org/2005/gmd&amp;elementSetName=full&amp;id={resources[i]["GeoCatID"]}"/>'

        body = [
            {
                "xpath": xpath_coupled,
                "value": f"<gn_add>{value_coupled}</gn_add>",
            },
            {
                "xpath": xpath_operates,
                "value": f"<gn_add>{value_operates}</gn_add>",
            },
        ]

        if geocat.edit_metadata(uuid=UUID, body=body)[0]:
            count += 1
            print(f"Resource added : {resources[i]['GeoCatID']}")
            print(f"{round((count/number - 1)*100, 2)}%")
        else:
            print(geocat.edit_metadata(uuid=UUID, body=body)[1])


def delete_all_coupled_resource(UUID):
    xpath_coupled = "/che:CHE_MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/srv:coupledResource"
    xpath_operates = "/che:CHE_MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/srv:operatesOn"

    body = [
        {
            "xpath": xpath_coupled,
            "value": f"<gn_delete></gn_delete>",
        },
        {
            "xpath": xpath_operates,
            "value": f"<gn_delete></gn_delete>",
        },
    ]

    if geocat.edit_metadata(uuid=UUID, body=body)[0]:
        print("All coupled resources have been deleted !")
    else:
        print(geocat.edit_metadata(uuid=UUID, body=body)[1])


getcap = get_getcapabilities_url(UUID)
layername_geocatid = get_layername_geocatid(getcap, 'https://api3.geo.admin.ch/rest/services/api/MapServer')
add_coupled_resources(UUID, layername_geocatid, len(layername_geocatid))
delete_all_coupled_resource(UUID)
