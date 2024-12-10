from lxml import etree
import requests
import logging
import os
import csv
import urllib.parse
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logs_dir = 'logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

####################################
# Link classification logic
####################################

class LinkUsage:
    API = 'api'
    MAP_API = 'mapapi'
    DOWNLOAD = 'download'
    DATA = 'data'
    GEODATA = 'geodata'
    LANDING_PAGE = 'landingpage'
    UNKNOWN = 'unknown'

def get_file_format(url: str):
    """Détermine le format de fichier à partir de l'extension dans l'URL."""
    url_lower = url.lower()
    if url_lower.endswith('.json'):
        return 'json'
    elif url_lower.endswith('.csv'):
        return 'csv'
    elif url_lower.endswith('.xls') or url_lower.endswith('.xlsx'):
        return 'excel'
    elif url_lower.endswith('.geojson'):
        return 'geojson'
    return None

def classify_link(protocol: str, url: str):
    """Détermine type et accessServiceProtocol basés sur protocol."""
    if protocol.startswith("OGC:"):
        type_ = 'service'
        prot_lower = protocol.lower()
        if 'wms' in prot_lower:
            accessServiceProtocol = 'wms'
        elif 'wmts' in prot_lower:
            accessServiceProtocol = 'wmts'
        elif 'wfs' in prot_lower:
            accessServiceProtocol = 'wfs'
        elif 'features' in prot_lower:
            accessServiceProtocol = 'ogcFeatures'
        else:
            accessServiceProtocol = None
    elif protocol.startswith("ESRI:"):
        type_ = 'service'
        accessServiceProtocol = 'esriRest'
    elif protocol.startswith("WWW:DOWNLOAD"):
        type_ = 'download'
        accessServiceProtocol = None
    elif protocol.startswith("WWW:LINK"):
        type_ = 'link'
        accessServiceProtocol = None
    elif protocol == "MAP:Preview":
        type_ = 'service'
        accessServiceProtocol = 'wms'  # on le traite comme un map API
    else:
        type_ = 'link'
        accessServiceProtocol = None

    return type_, accessServiceProtocol

def get_usages_for_link(protocol: str, url: str):
    """Reproduit la logique du LinkClassifierService."""
    type_, accessServiceProtocol = classify_link(protocol, url)

    if type_ == 'service':
        if accessServiceProtocol in ['esriRest', 'wfs', 'ogcFeatures']:
            return [LinkUsage.API, LinkUsage.DOWNLOAD, LinkUsage.GEODATA]
        elif accessServiceProtocol in ['wms', 'wmts']:
            return [LinkUsage.API, LinkUsage.MAP_API]
        else:
            return [LinkUsage.UNKNOWN]
    elif type_ == 'download':
        fmt = get_file_format(url)
        if fmt in ['json', 'csv', 'excel']:
            return [LinkUsage.DOWNLOAD, LinkUsage.DATA]
        elif fmt == 'geojson':
            return [LinkUsage.DOWNLOAD, LinkUsage.GEODATA]
        else:
            # Si '/wfs' dans l'URL alors geodata
            if '/wfs' in url.lower():
                return [LinkUsage.DOWNLOAD, LinkUsage.GEODATA]
            return [LinkUsage.DOWNLOAD]
    else:
        return [LinkUsage.UNKNOWN]

def has_usage(protocol: str, url: str, usage: str):
    return usage in get_usages_for_link(protocol, url)

####################################
# Network fetch functions
####################################

def clean_service_url(url, protocol):
    """Nettoie l'URL pour WMS/WMTS."""
    if protocol in ['OGC:WMS', 'OGC:WMTS']:
        if '?' not in url:
            url += '?'
        elif not url.endswith('&') and not url.endswith('?'):
            url += '&'
        if 'SERVICE=' not in url.upper():
            if protocol == 'OGC:WMS':
                url += 'SERVICE=WMS&'
            elif protocol == 'OGC:WMTS':
                url += 'SERVICE=WMTS&'
        if 'VERSION=' not in url.upper():
            url += 'VERSION=1.3.0&'
        if 'REQUEST=' not in url.upper():
            url += 'REQUEST=GetCapabilities'
    return url

def fetch_capabilities_wms_wmts(url):
    """Récupère le GetCapabilities pour WMS/WMTS."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        if "ServiceExceptionReport" in response.text or "Can't parse XML request" in response.text:
            logger.error(f"Service Exception détectée dans GetCapabilities pour l'URL : {url}")
            return None
        content_type = response.headers.get("Content-Type", "").lower()
        if "xml" not in content_type and "text" not in content_type:
            logger.error(f"Contenu non valide (non XML) pour {url} : {content_type}")
            return None
        return response.text
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la récupération de GetCapabilities depuis {url} : {e}")
        return None

def fetch_esri_rest(url):
    """Effectue une requête sur un service ESRI REST."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()
        if "json" not in content_type and "text" not in content_type:
            logger.error(f"Contenu non valide (non JSON) pour {url} : {content_type}")
            return None

        return response.text
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la récupération du service ESRI REST depuis {url} : {e}")
        return None

def check_metadata_service_url(index: dict, valid_url: list) -> dict:
    # Extraction du titre et de l'UUID
    resource_title = index["_source"].get("resourceTitleObject", {}).get("default", "No Title Available")
    uuid = index["_source"].get("uuid", "No UUID")
    logger.debug(f"Extracted Title: {resource_title}, UUID: {uuid}")

    # Initialisation
    organization_name = "No Organization Available"
    email_address = "No Email Available"

    # Récupération de l'email/org depuis contactForResource
    if "contactForResource" in index["_source"]:
        for user in index["_source"]["contactForResource"]:
            if "email" in user:
                email_address = user["email"]
            if "organisationObject" in user:
                org_candidate = user["organisationObject"].get("default")
                if org_candidate:
                    organization_name = org_candidate
            if organization_name != "No Organization Available" and email_address != "No Email Available":
                break

    result = {
        "uuid": uuid,
        "title": resource_title,
        "organization": organization_name,
        "email": email_address,
        "errors": list()
    }

    new_valid_url = []
    invalid_urls = []

    if "link" in index["_source"]:
        for link_item in index["_source"]["link"]:
            protocol = link_item.get("protocol", "")
            for lang, url_value in link_item.get("urlObject", {}).items():
                capabilities_content = None
                cleaned_url = url_value

                # Si c'est un service WMS/WMTS
                if protocol in ['OGC:WMS', 'OGC:WMTS']:
                    cleaned_url = clean_service_url(url_value, protocol)
                    if cleaned_url in valid_url:
                        continue
                    capabilities_content = fetch_capabilities_wms_wmts(cleaned_url)
                    if not capabilities_content:
                        # Tentative via proxy
                        proxy_url = "https://www.geocat.ch/geonetwork/proxy?url=" + urllib.parse.quote(cleaned_url, safe='')
                        logger.debug(f"Tentative via le proxy Geonetwork : {proxy_url}")
                        capabilities_content = fetch_capabilities_wms_wmts(proxy_url)

                elif protocol == 'ESRI:REST':
                    # Essayer de récupérer le service ESRI REST
                    capabilities_content = fetch_esri_rest(cleaned_url)

                # Vérification pour WMS/WMTS/ESRI:REST
                if protocol in ['OGC:WMS', 'OGC:WMTS', 'ESRI:REST']:
                    if not capabilities_content:
                        if cleaned_url not in invalid_urls:
                            invalid_urls.append(cleaned_url)
                            result["errors"].append({
                                "uuid": result["uuid"],
                                "title": result["title"],
                                "organization": result["organization"],
                                "email": result["email"],
                                "error_message": f"Invalid service URL for {protocol} protocol",
                                "invalid_url": cleaned_url,
                            })
                            logger.error(f"Invalid URL: {cleaned_url} - ServiceType: {protocol}")
                        continue
                    new_valid_url.append(cleaned_url)
                    valid_url.append(cleaned_url)
                # Pour les autres liens (download, link), on ne teste pas le service.

    else:
        logger.warning("No links found in the metadata record.")

    return result, new_valid_url

def write_errors_to_csv(errors):
    csv_file = os.path.join(logs_dir, f"invalid_ogc_urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    csv_columns = ['UUID', 'Title', 'Organization', 'Email', 'Error Message', 'Invalid URL']
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for error in errors:
                writer.writerow({
                    'UUID': error.get('uuid', 'No UUID'),
                    'Title': error.get('title', 'No Title'),
                    'Organization': error.get('organization', 'No Organization'),
                    'Email': error.get('email', 'No Email'),
                    'Error Message': error.get('error_message', ''),
                    'Invalid URL': error.get('invalid_url', '')
                })
        logger.info(f"CSV file created: {csv_file}")
    except IOError:
        logger.error("I/O error while writing the CSV file.")
