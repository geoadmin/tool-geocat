import os
from dotenv import load_dotenv

load_dotenv()
# Define your environment variables in a .env file
GEOCAT_USERNAME = os.getenv('GEOCAT_USERNAME')
GEOCAT_PASSWORD = os.getenv('GEOCAT_PASSWORD')
PROXY_HTTP = os.getenv('HTTP_PROXY')
PROXY_HTTPS = os.getenv('HTTPS_PROXY')

ENVIRONMENT = 'INT'  # Default environment
API_URLS = {
    'PROD': 'https://geocat.ch/geonetwork/srv/api',
    'INT': 'https://geocat-int.dev.bgdi.ch/geonetwork/srv/api',
    'DEV': 'https://geocat-dev.dev.bgdi.ch/geonetwork/srv/api'
}
API_URL = API_URLS.get(ENVIRONMENT)

# Page size for server-side search requests
SEARCH_PAGE_SIZE = 200

# Query used by the server search (GeoNetwork/ElasticSearch query_string).
# Filter: non-harvested, invalid (0 = invalid, -1 = not yet validated),
# exclude internal groups (42, 55, 50000150), published records.
SERVER_SEARCH_QUERY = {
    "isHarvested": {"false": True},
    #"valid": {"0": True, "-1": True},
    "groupOwner": {"42": False, "55": False, "50000150": False},
    # "isPublishedToAll": {"true": True}
}

PARAMETER_UUID_PROCESSING = 'OVERWRITE'
TRANSFORMATION_TO_ECH0271='schema:iso19115-3.2018.che:convert/fromISO19139.che'
PARAMETER_GROUP = '42'  # Group ID for XML files
PARAMETER_VALIDATION = False
PARAMETER_PUBLICATION = True
PATH_TO_MD_FILES = r'\\v0t0020a.adr.admin.ch\prod\kogis\igks\geocat\Metadatenapplikation geocat.ch entwickeln und betreiben (463)\Software geocat.ch entwickeln\Betrieb Applikation geocat.ch\XML Backup\20251203_prod\GeocatBackup_20251203-132543\metadata'
UPDATE_DATE_STAMP = True
ASSIGN_TO_CATALOG = True