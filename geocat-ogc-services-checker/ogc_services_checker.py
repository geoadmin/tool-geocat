from lxml import etree
import requests
import logging
import os
import csv
from datetime import datetime

# Configurer le logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuration des protocoles OGC
class config:
    OGC_PROTOCOLS = ['OGC:WMS', 'OGC:WMTS', 'ESRI:REST']

# Répertoire pour les logs
logs_dir = 'logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

def clean_service_url(url, protocol):
    if '?' not in url:
        url += '?'
    elif not url.endswith('&') and not url.endswith('?'):
        url += '&'
    if 'SERVICE=' not in url:
        if protocol == 'OGC:WMS':
            url += 'SERVICE=WMS&'
        elif protocol == 'OGC:WMTS':
            url += 'SERVICE=WMTS&'
    if 'VERSION=' not in url:
        url += 'VERSION=1.3.0&'
    if 'REQUEST=' not in url:
        url += 'REQUEST=GetCapabilities'
    return url

def fetch_capabilities(url):
    """Récupère le contenu GetCapabilities."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la récupération de GetCapabilities depuis {url} : {e}")
        return None

def check_metadata_service_url(index: dict, valid_url: list) -> dict:
    """Vérifie si les URLs de service OGC des métadonnées sont valides."""

    # Extraction du titre
    resource_title = index["_source"].get("resourceTitleObject", {}).get("default", "No Title Available")
    logger.debug(f"Extracted Title: {resource_title}")

    # Extraction de l'email
    email = "No Email Available"

    if "contactForResource" in index["_source"]:
        for user in index["_source"]["contactForResource"]:
            email = user.get("email", "No Email Available")
            logger.debug(f"Extracted Email: {email}")
            break  # Arrêtez après avoir trouvé le premier email

    result = {
        "uuid": index["_source"].get("uuid", "No UUID"),
        "title": resource_title,
        "email": email,
        "errors": list()
    }

    new_valid_url = []
    invalid_urls = []

    if "link" in index["_source"]:
        for i in index["_source"]["link"]:
            if i["protocol"] in config.OGC_PROTOCOLS:
                for lang, url in i["urlObject"].items():
                    cleaned_url = clean_service_url(url, i["protocol"])

                    if cleaned_url in valid_url:
                        continue

                    capabilities_content = fetch_capabilities(cleaned_url)

                    if not capabilities_content:
                        if cleaned_url not in invalid_urls:
                            invalid_urls.append(cleaned_url)
                            result["errors"].append({
                                "uuid": result["uuid"],
                                "title": result["title"],
                                "email": result["email"],
                                "error_message": f"Invalid service URL for {i['protocol']} protocol",
                                "invalid_url": cleaned_url,
                            })
                            logger.error(f"Invalid URL: {cleaned_url} - ServiceType: {i['protocol']}")
                        continue

                    new_valid_url.append(cleaned_url)
                    valid_url.append(cleaned_url)
    else:
        logger.warning("No links found in the metadata record.")

    return result, new_valid_url

def write_errors_to_csv(errors):
    csv_file = os.path.join(logs_dir, f"invalid_ogc_urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    csv_columns = ['UUID', 'Title', 'Email', 'Error Message', 'Invalid URL']

    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for error in errors:
                writer.writerow({
                    'UUID': error.get('uuid', 'No UUID'),
                    'Title': error.get('title', 'No Title'),
                    'Email': error.get('email', 'No Email'),
                    'Error Message': error.get('error_message', ''),
                    'Invalid URL': error.get('invalid_url', '')
                })
        logger.info(f"CSV file created: {csv_file}")
    except IOError:
        logger.error("I/O error while writing the CSV file.")
