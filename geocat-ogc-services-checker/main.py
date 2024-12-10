import os
import logging
from dotenv import load_dotenv
import geopycat
import config
import ogc_services_checker
from datetime import datetime
import csv

# Load environment variables from .env file
load_dotenv()

logs_dir = os.path.join(os.path.dirname(__file__), "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
logfile = os.path.join(logs_dir, f"ogc_urls_{timestamp}.log")

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(logfile)]
)

logger = logging.getLogger(__name__)

geocat = geopycat.geocat(env="prod")
os.environ["HTTP_PROXY"] = geocat.session.proxies.get("http", "")
os.environ["HTTPS_PROXY"] = geocat.session.proxies.get("https", "")

# Path for the CSV files
valid_csv_file = os.path.join(logs_dir, f"valid_ogc_urls_{timestamp}.csv")
invalid_csv_file = os.path.join(logs_dir, f"invalid_ogc_urls_{timestamp}.csv")

valid_csv_columns = ['UUID', 'Title', 'Email', 'Valid URL']
invalid_csv_columns = ['UUID', 'Title', 'Email', 'Error Message', 'Invalid URL', 'Missing Layer Name']

def initialize_csv(file_path, columns):
    """Initialize a CSV file with headers."""
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
        logger.info(f"CSV file initialized: {file_path}")
    except IOError as e:
        logger.error(f"Error initializing CSV file {file_path}: {e}")

def append_to_csv(file_path, data, columns):
    """Append a single row of data to the CSV file."""
    try:
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writerow(data)
    except IOError as e:
        logger.error(f"Error writing to CSV file {file_path}: {e}")

def get_metadata():
    try:
        response = geocat.es_deep_search(body=config.SEARCH_API_BODY)
        if not response:
            logger.error("No metadata records found")
            return []
        return response
    except Exception as e:
        logger.error(f"Error fetching metadata records: {e}")
        return []

def main():
    # Initialize CSV files
    initialize_csv(valid_csv_file, valid_csv_columns)
    initialize_csv(invalid_csv_file, invalid_csv_columns)

    metadata_records = get_metadata()
    if not metadata_records:
        logger.error("No metadata records found or an error occurred during retrieval.")
        return

    valid_urls = []

    for record in metadata_records:
        logger.info(f"Processing metadata UUID: {record['_source']['uuid']}")
        result, new_valid_urls = ogc_services_checker.check_metadata_service_url(record, valid_urls)
        valid_urls.extend(new_valid_urls)

        # Process valid URLs
        for url in new_valid_urls:
            valid_data = {
                'UUID': record['_source']['uuid'],
                'Title': result['title'],
                'Email': result['email'],
                'Valid URL': url
            }
            append_to_csv(valid_csv_file, valid_data, valid_csv_columns)

        # Process errors
        for error in result["errors"]:
            error_data = {
                'UUID': record['_source']['uuid'],
                'Title': result['title'],
                'Email': result['email'],
                'Error Message': error['error_message'],
                'Invalid URL': error['invalid_url'],
                'Missing Layer Name': error.get('missing_layer_name', '')
            }
            append_to_csv(invalid_csv_file, error_data, invalid_csv_columns)

if __name__ == "__main__":
    main()
