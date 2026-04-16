import os
import requests
import json
import logging
import sys
import csv
import config

def setup_logging(debug: bool = False):
    """Configure logging"""
    logging_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True  # Remove existing handlers to avoid duplicate log entries
    )

class GeoNetworkValidationAnalyzer:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = (username, password)
        
        # Configure proxy if defined
        if config.PROXY_HTTP or config.PROXY_HTTPS:
            self.session.proxies = {
                'http': config.PROXY_HTTP,
                'https': config.PROXY_HTTPS
            }
        
        
    def authenticate(self) -> bool:
        """Authenticate and retrieve the XSRF token"""
        try:
            response = self.session.get(
                f"{self.base_url}/me",
                headers={"accept": "application/json"}
            )
            response.raise_for_status()
            
            xsrf_token = response.cookies.get("XSRF-TOKEN")
            if xsrf_token:
                self.session.headers.update({
                    "X-XSRF-TOKEN": xsrf_token,
                    "accept": "application/json"
                })
                logging.info("✅ Successfully authenticated")
                return True
            else:
                logging.error("❌ XSRF token not found")
                return False
                
        except Exception as e:
            logging.error(f"❌ Authentication failed: {e}")
            return False
    
    def fetch_contact_info(self, uuids: List[str], batch_size: int = 200) -> Dict[str, Dict[str, str]]:
        """
        Retrieve the organisation and email of the contact for a list of UUIDs
        via POST /search/records/_search.

        Args:
            uuids: List of UUIDs to query
            batch_size: Number of UUIDs per ES request

        Returns:
            Dict uuid → {'organisation': str, 'email': str}
        """
        contact_map: Dict[str, Dict[str, str]] = {}

        for i in range(0, len(uuids), batch_size):
            batch = uuids[i:i + batch_size]

            payload = {
                "query": {
                    "terms": {
                        "uuid": batch
                    }
                },
                "_source": {
                    "includes": [
                        "uuid",
                        "contact.organisationObject.default",
                        "contact.email"
                    ]
                },
                "size": len(batch)
            }

            try:
                resp = self.session.post(
                    f"{self.base_url}/search/records/_search",
                    params={"bucket": "metadata"},
                    json=payload
                )
                resp.raise_for_status()
                data = resp.json()

                for hit in data.get('hits', {}).get('hits', []):
                    source = hit.get('_source', {})
                    uuid = source.get('uuid') or hit.get('_id', '')
                    if not uuid:
                        continue

                    org = ''
                    email = ''
                    contacts = source.get('contact', [])

                    # contact can be a list or a single dict
                    if isinstance(contacts, list) and contacts:
                        first = contacts[0]
                    elif isinstance(contacts, dict):
                        first = contacts
                    else:
                        first = {}

                    if first:
                        org_obj = first.get('organisationObject', {})
                        if isinstance(org_obj, dict):
                            org = org_obj.get('default', '')
                        raw_email = first.get('email', '')
                        # email can be a list ['addr@example.com'] or a plain string
                        if isinstance(raw_email, list):
                            email = raw_email[0] if raw_email else ''
                        else:
                            email = str(raw_email)

                    contact_map[uuid] = {
                        'organisation': org or '',
                        'email': email or ''
                    }

            except Exception as e:
                logging.error(f"❌ Error retrieving contacts (batch {i//batch_size + 1}): {e}")

        logging.info(f"📋 Contact information retrieved for {len(contact_map)}/{len(uuids)} records")
        return contact_map

    def generate_csv_report(self, validation_data: List[Dict[str, Any]],
                            output_file: str = "validation_errors.csv",
                            contact_info: Dict[str, Dict[str, str]] = None):
        """
        Generate a CSV file with errors per UUID.

        Args:
            validation_data: Validation results
            output_file: Output CSV file path
            contact_info: Dict uuid → {'organisation': str, 'email': str} (optional)
        """
        include_contact = contact_info is not None
        fieldnames = ['uuid']
        if include_contact:
            fieldnames += ['organisation', 'email']
        fieldnames += ['error_count', 'errors_list', 'error_details']

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for record in validation_data:
                uuid = record['uuid']
                errors = record.get('errors', [])
                error_count = record.get('error_count', 0)

                # Format errors
                errors_list = "; ".join([str(e).replace('\n', ' ').replace('\r', '')
                                        for e in errors[:10]])  # Limit to 10 errors
                error_details = json.dumps(errors, ensure_ascii=False)

                row = {'uuid': uuid}
                if include_contact:
                    info = contact_info.get(uuid, {})
                    row['organisation'] = info.get('organisation', '')
                    row['email'] = info.get('email', '')
                row['error_count'] = error_count
                row['errors_list'] = errors_list[:500]  # Limit string length
                row['error_details'] = error_details

                writer.writerow(row)

        logging.info(f"💾 CSV file generated: {output_file}")
    
    def generate_error_statistics(self, validation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate detailed statistics on validation errors.
        """
        # Collect all errors
        all_errors = []
        error_counter = Counter()
        records_with_errors = 0
        total_errors = 0
        
        for record in validation_data:
            errors = record.get('errors', [])
            if errors:
                records_with_errors += 1
                total_errors += len(errors)
                
                for error in errors:
                    # Clean and normalise the error message
                    error_str = str(error).strip()
                    all_errors.append({
                        'uuid': record['uuid'],
                        'error': error_str
                    })
                    error_counter[error_str] += 1
        
        # Statistics
        total_records = len(validation_data)
        records_without_errors = total_records - records_with_errors
        
        # Most frequent errors
        most_common_errors = error_counter.most_common(20)
        
        # Group errors by pattern
        error_patterns = {}
        for error, count in error_counter.items():
            # Extract a simple pattern (first word or first sentence)
            pattern = error.split('.')[0] if '.' in error else error.split()[0] if error else "Unknown"
            if pattern not in error_patterns:
                error_patterns[pattern] = {'count': 0, 'examples': []}
            error_patterns[pattern]['count'] += count
            if len(error_patterns[pattern]['examples']) < 3:
                error_patterns[pattern]['examples'].append(error)
        
        # Sort patterns by frequency
        sorted_patterns = sorted(error_patterns.items(), 
                               key=lambda x: x[1]['count'], 
                               reverse=True)
        
        statistics = {
            'total_records': total_records,
            'records_with_errors': records_with_errors,
            'records_without_errors': records_without_errors,
            'total_errors': total_errors,
            'average_errors_per_record': total_errors / total_records if total_records > 0 else 0,
            'error_rate': (records_with_errors / total_records) * 100 if total_records > 0 else 0,
            'most_common_errors': most_common_errors,
            'error_patterns': dict(sorted_patterns[:10]),  # Top 10 patterns
            'all_errors': all_errors
        }
        
        return statistics
    
    def save_statistics_report(self, statistics: Dict[str, Any], 
                             output_file: str = "validation_statistics.json"):
        """Save statistics to a JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, indent=2, ensure_ascii=False)
        
        logging.info(f"💾 Statistics saved: {output_file}")
    
    def generate_summary_report(self, statistics: Dict[str, Any], 
                              output_file: str = "validation_summary.txt"):
        """Generates a summary text report"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("METADATA VALIDATION REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Environment: {config.ENVIRONMENT}\n\n")
            
            f.write("📊 GLOBAL STATISTICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total records analysed: {statistics['total_records']}\n")
            f.write(f"Records with errors: {statistics['records_with_errors']} "
                   f"({statistics['error_rate']:.1f}%)\n")
            f.write(f"Records without errors: {statistics['records_without_errors']}\n")
            f.write(f"Total errors: {statistics['total_errors']}\n")
            f.write(f"Average errors per record: {statistics['average_errors_per_record']:.2f}\n\n")
            
            f.write("🚨 MOST FREQUENT ERRORS\n")
            f.write("-" * 40 + "\n")
            for i, (error, count) in enumerate(statistics['most_common_errors'][:15], 1):
                f.write(f"{i:2d}. [{count} records] {error[:100]}...\n")
            
            f.write("\n🔍 ERROR PATTERNS (TOP 10)\n")
            f.write("-" * 40 + "\n")
            for pattern, data in list(statistics['error_patterns'].items())[:10]:
                f.write(f"\n• {pattern}\n")
                f.write(f"  Affects {data['count']} occurrences\n")
                f.write(f"  Examples:\n")
                for example in data['examples'][:2]:
                    f.write(f"    - {example[:80]}...\n")
            
            f.write("\n" + "=" * 60 + "\n")
        
        logging.info(f"📝 Summary report generated: {output_file}")
    
    def generate_error_distribution_csv(self, statistics: Dict[str, Any],
                                      output_file: str = "error_distribution.csv"):
        """Generate a CSV with error distribution"""
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['error_message', 'occurrence_count', 'affected_records_percentage', 'example']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            total_records = statistics['total_records']
            
            for error_msg, count in statistics['most_common_errors']:
                percentage = (count / total_records) * 100 if total_records > 0 else 0
                
                writer.writerow({
                    'error_message': error_msg[:200],  # Limit string length
                    'occurrence_count': count,
                    'affected_records_percentage': f"{percentage:.1f}%",
                    'example': error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                })
        
        logging.info(f"📈 Error distribution CSV generated: {output_file}")

    # ──────────────────────────────────────────────────────────────────
    # Individual validation (XSD + Schematron) via PUT /records/{uuid}/validate/internal
    # ──────────────────────────────────────────────────────────────────

    def extract_detailed_errors(self, validation_report: Dict[str, Any]) -> List[str]:
        """
        Extract detailed errors from a validation report.
        Handles the metadataErrors structure returned by PUT /records/{uuid}/validate.

        Args:
            validation_report: Report returned by /records/{uuid}/validate

        Returns:
            List of detailed error messages
        """
        detailed_errors = []
        
        if not validation_report:
            return detailed_errors
        
        # Main structure: metadataErrors (same as batch validate)
        # { "metadataErrors": { "<internalId>": [ { "uuid": "...", "message": "..." } ] } }
        if 'metadataErrors' in validation_report:
            metadata_errors = validation_report.get('metadataErrors', {})
            for record_id, error_list in metadata_errors.items():
                if not isinstance(error_list, list):
                    continue
                for error_item in error_list:
                    if isinstance(error_item, dict):
                        message = error_item.get('message', '') or error_item.get('error', '') or str(error_item)
                        # Ignore the generic "Is invalid" message
                        if message and not message.endswith('Is invalid'):
                            rule = error_item.get('rule', '') or error_item.get('ruleId', '')
                            xpath = error_item.get('xpath', '') or error_item.get('xPath', '')
                            error_text = message
                            if rule:
                                error_text += f" [Rule: {rule}]"
                            if xpath:
                                error_text += f" (XPath: {xpath})"
                            detailed_errors.append(error_text)
                    else:
                        msg = str(error_item)
                        if msg and not msg.endswith('Is invalid'):
                            detailed_errors.append(msg)
            return detailed_errors
        
        # Structure 2: validationErrors
        if 'validationErrors' in validation_report:
            for error in validation_report.get('validationErrors', []):
                if isinstance(error, dict):
                    message = error.get('message', '') or error.get('error', '') or str(error)
                    xpath = error.get('xpath', '')
                    rule = error.get('rule', '')
                    error_text = message
                    if xpath:
                        error_text += f" (XPath: {xpath})"
                    if rule:
                        error_text += f" [Rule: {rule}]"
                    detailed_errors.append(error_text)
                else:
                    detailed_errors.append(str(error))
            return detailed_errors
        
        # Structure 3: root-level errors
        if 'errors' in validation_report:
            for error in validation_report.get('errors', []):
                if isinstance(error, dict):
                    message = error.get('message', '') or error.get('description', '') or str(error)
                    detailed_errors.append(message)
                else:
                    detailed_errors.append(str(error))
            return detailed_errors
        
        # Structure 4: Schematron report (response of PUT /validate/internal)
        # rule_type can be "failure", "error" or "fatal"
        if 'report' in validation_report:
            for section in validation_report.get('report', []):
                section_label = section.get('label') or section.get('id', 'schematron')
                for pattern in section.get('patterns', {}).get('pattern', []):
                    pattern_title = pattern.get('title', 'Unknown pattern')
                    for rule in pattern.get('rules', {}).get('rule', []):
                        rule_type = rule.get('type', 'error')
                        if rule_type.lower() in ['error', 'fatal', 'failure']:
                            rule_msg = rule.get('msg', '')
                            rule_details = rule.get('details', '')
                            error_text = f"[{section_label}] {pattern_title} -> {rule_msg}"
                            if rule_details:
                                error_text += f" (xpath: {rule_details})"
                            detailed_errors.append(error_text)
            return detailed_errors
        
        # Structure 5: simple validation
        if 'validation' in validation_report:
            validation = validation_report.get('validation', {})
            if isinstance(validation, dict) and validation.get('status') == 'invalid':
                for msg in validation.get('messages', []):
                    detailed_errors.append(msg.get('message', str(msg)) if isinstance(msg, dict) else str(msg))
        
        return detailed_errors

    # ──────────────────────────────────────────────────────────────────
    # Individual validation (XSD + Schematron) via PUT /records/{uuid}/validate
    # ──────────────────────────────────────────────────────────────────

    def _parse_validate_report(self, uuid: str, report: Any) -> List[str]:
        """
        Parse the response of PUT /records/{uuid}/validate.
        Handles several possible response structures (list or dict).
        Returns the deduplicated list of error messages (XSD + Schematron).
        """
        errors: List[str] = []
        seen: set = set()

        def add(msg: str) -> None:
            msg = msg.strip()
            if msg and msg not in seen and not msg.endswith('Is invalid'):
                seen.add(msg)
                errors.append(msg)

        if not report:
            return errors

        # ── Structure 1: list of validation objects (GeoNetwork 4.x) ──
        # [{"valType": "xsd", "valid": 0, "errors": [...]},
        #  {"valType": "schematron", "schematronErrors": [...]}]
        if isinstance(report, list):
            for val_obj in report:
                if not isinstance(val_obj, dict):
                    continue
                val_type = val_obj.get('valType') or val_obj.get('type', 'unknown')
                val_valid = val_obj.get('valid', 1)
                if val_valid == 1:  # 1 = valid, no errors
                    continue

                # Direct errors
                for err in val_obj.get('errors', []):
                    if isinstance(err, dict):
                        add(err.get('message') or err.get('msg') or str(err))
                    else:
                        add(str(err))

                # Schematron errors (schematronErrors[].errors[])
                for sch in val_obj.get('schematronErrors', []):
                    if not isinstance(sch, dict):
                        continue
                    sch_name = sch.get('name') or sch.get('ruleId') or val_type
                    # Errors in an array
                    for sch_err in sch.get('errors', []):
                        if isinstance(sch_err, dict):
                            msg = sch_err.get('message') or sch_err.get('msg') or str(sch_err)
                            location = sch_err.get('location') or sch_err.get('xpath') or ''
                            full = f"[{sch_name}] {msg}"
                            if location:
                                full += f" (xpath: {location})"
                            add(full)
                        else:
                            add(f"[{sch_name}] {str(sch_err)}")
                    # Plain text / HTML report
                    report_text = sch.get('report') or sch.get('message') or ''
                    if report_text and not sch.get('errors'):
                        if '<' in report_text:
                            try:
                                from lxml import html as _lhtml
                                tree = _lhtml.fromstring(report_text)
                                for elem in tree.xpath(
                                    '//*[contains(@class,"failure") or contains(@class,"error") '
                                    'or contains(@class,"svrl")]'
                                ):
                                    add(f"[{sch_name}] {elem.text_content().strip()}")
                            except Exception:
                                add(f"[{sch_name}] {report_text[:300]}")
                        else:
                            add(f"[{sch_name}] {report_text[:300]}")

            if errors:
                return errors

        # ── Structure 2: dict with metadataErrors (same as batch) ──
        if isinstance(report, dict):
            for record_id, error_list in report.get('metadataErrors', {}).items():
                for err in (error_list or []):
                    if isinstance(err, dict):
                        add(err.get('message') or str(err))
                    else:
                        add(str(err))

            for err in report.get('xsdErrors', []):
                if isinstance(err, dict):
                    add(err.get('message') or str(err))
                else:
                    add(str(err))

            for sch in report.get('schematronErrors', []):
                if isinstance(sch, dict):
                    name = sch.get('name', 'schematron')
                    for err in sch.get('errors', []):
                        if isinstance(err, dict):
                            msg = err.get('message') or err.get('msg') or str(err)
                            add(f"[{name}] {msg}")
                        else:
                            add(f"[{name}] {str(err)}")

            if errors:
                return errors

        # ── Fallback: extract_detailed_errors() for legacy structures ──
        return self.extract_detailed_errors(report) if isinstance(report, dict) else errors

    def validate_single_record(self, uuid: str) -> Dict[str, Any]:
        """
        Validate a single record with full XSD and Schematron errors.

        Flow:
          1. GET  /records/{uuid}/editor          → open editing session
          2. PUT  /records/{uuid}/validate/internal → return Schematron errors
          3. DELETE /records/{uuid}/editor         → close editing session

        Args:
            uuid: Metadata record UUID

        Returns:
            Dictionary {uuid, errors, has_errors, error_count}
        """
        editor_url = f"{self.base_url}/records/{uuid}/editor"
        editor_opened = False

        try:
            # ── Step 1: Open editing session ──────────────────────────────
            r_open = self.session.get(
                editor_url,
                headers={"accept": "text/html,application/xhtml+xml,*/*"}
            )
            if r_open.status_code not in [200, 201]:
                logging.warning(f"⚠️ Unable to open editor for {uuid}: HTTP {r_open.status_code}")
                return {
                    'uuid': uuid,
                    'errors': [f"Editor HTTP {r_open.status_code}"],
                    'has_errors': True,
                    'error_count': 1
                }
            editor_opened = True

            # ── Step 2: Internal validation (XSD + Schematron) ────────────
            r_val = self.session.put(
                f"{self.base_url}/records/{uuid}/validate/internal",
                headers={"accept": "application/json"}
            )
            if r_val.status_code not in [200, 201]:
                logging.warning(f"⚠️ validate/internal HTTP {r_val.status_code} for {uuid}")
                return {
                    'uuid': uuid,
                    'errors': [f"validate/internal HTTP {r_val.status_code}"],
                    'has_errors': True,
                    'error_count': 1
                }

            report = r_val.json()
            logging.debug(f"📋 validate/internal response for {uuid}: {json.dumps(report, ensure_ascii=False)[:500]}")
            errors = self._parse_validate_report(uuid, report)

            return {
                'uuid': uuid,
                'errors': errors,
                'has_errors': len(errors) > 0,
                'error_count': len(errors)
            }

        except Exception as e:
            logging.error(f"❌ Validation error for {uuid}: {e}")
            return {
                'uuid': uuid,
                'errors': [f"Exception: {str(e)}"],
                'has_errors': True,
                'error_count': 1
            }

        finally:
            # ── Step 3: Close editing session (always) ─────────────────────
            if editor_opened:
                try:
                    self.session.delete(
                        editor_url,
                        params={"withChanges": "false"},
                        headers={"accept": "text/html,application/xhtml+xml,*/*"}
                    )
                except Exception:
                    pass  # Non-blocking

    def validate_all_individually(self, uuids: List[str]) -> List[Dict[str, Any]]:
        """
        Validate each record individually via PUT /records/{uuid}/validate.
        Slower than batch validation but captures full XSD and Schematron errors
        in a single call per record.

        Args:
            uuids: List of UUIDs to validate

        Returns:
            List of validation results per record
        """
        results: List[Dict[str, Any]] = []
        total = len(uuids)

        for i, uuid in enumerate(uuids, 1):
            result = self.validate_single_record(uuid)
            results.append(result)

            if result['has_errors']:
                logging.info(
                    f"⚠️ [{i}/{total}] {uuid}: {result['error_count']} error(s)"
                )
            else:
                if i % 50 == 0 or i == total:
                    logging.info(
                        f"✅ [{i}/{total}] {(i / total) * 100:.1f}% processed – "
                        f"{sum(1 for r in results if not r['has_errors'])} valid, "
                        f"{sum(1 for r in results if r['has_errors'])} with errors"
                    )

        return results

    def _build_query_string_from_dict(self, query_dict: Dict[str, Any]) -> str:
        """
        Convert the filter dictionary (from SERVER_SEARCH_QUERY) into a
        Lucene/ElasticSearch query string.

        Example:
            {"isHarvested": {"false": True}, "valid": {"0": True, "-1": True},
             "groupOwner": {"42": False, "55": False}}
        →  '(isHarvested:"false") AND (valid:"0" OR valid:"-1") AND
            (-groupOwner:"42" OR -groupOwner:"55")'
        """
        parts = []
        for field, values in query_dict.items():
            if not isinstance(values, dict):
                continue

            include_vals = [v for v, flag in values.items() if flag is True]
            exclude_vals = [v for v, flag in values.items() if flag is False]

            if include_vals:
                clause = " OR ".join(f'{field}:"{v}"' for v in include_vals)
                parts.append(f"({clause})")

            if exclude_vals:
                clause = " OR ".join(f'-{field}:"{v}"' for v in exclude_vals)
                parts.append(f"({clause})")

        return " AND ".join(parts)

    def _extract_uuids_from_search_result(self, data: Any) -> List[str]:
        """Extract UUIDs from an ElasticSearch response (hits.hits[]._source.uuid)."""
        uuids = []
        if not isinstance(data, dict):
            return uuids

        hits_root = data.get('hits', {})
        if isinstance(hits_root, dict):
            hit_list = hits_root.get('hits', [])
        elif isinstance(hits_root, list):
            hit_list = hits_root
        else:
            return uuids

        for hit in hit_list:
            if not isinstance(hit, dict):
                continue
            source = hit.get('_source', {})
            if isinstance(source, dict):
                uuid = source.get('uuid') or source.get('id')
                if uuid:
                    uuids.append(str(uuid))
                    continue
            # Fall back to _id
            uid = hit.get('_id')
            if uid:
                uuids.append(str(uid))

        return uuids

    def search_records(self, query: Dict[str, Any], page_size: int = 100) -> List[str]:
        """
        Search for records via the GeoNetwork ElasticSearch API
        (POST /search/records/_search) with automatic result pagination.

        Args:
            query: filter dictionary (SERVER_SEARCH_QUERY)
            page_size: number of items per page (ES batch size)

        Returns:
            List of UUIDs found
        """
        uuids: List[str] = []
        from_offset = 0

        query_string = self._build_query_string_from_dict(query)
        logging.info(f"🔎 Lucene query: {query_string}")

        while True:
            payload = {
                "from": from_offset,
                "size": page_size,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "query_string": {
                                    "query": query_string,
                                    "default_operator": "AND"
                                }
                            },
                            {
                                "terms": {
                                    "isTemplate": ["n"]
                                }
                            }
                        ]
                    }
                },
                "_source": ["uuid"]
            }

            try:
                resp = self.session.post(
                    f"{self.base_url}/search/records/_search",
                    params={"bucket": "s101"},
                    json=payload
                )
                resp.raise_for_status()
                data = resp.json()

                page_uuids = self._extract_uuids_from_search_result(data)
                if not page_uuids:
                    break

                uuids.extend(page_uuids)

                # Check ES total to stop pagination
                total_info = data.get('hits', {}).get('total', {})
                if isinstance(total_info, dict):
                    total = total_info.get('value', 0)
                elif isinstance(total_info, int):
                    total = total_info
                else:
                    total = len(uuids)

                if len(page_uuids) < page_size or from_offset + page_size >= total:
                    break

                from_offset += page_size

            except Exception as e:
                logging.error(f"❌ Error searching for records: {e}")
                break

        logging.info(f"🔎 {len(uuids)} records found for the query")
        return uuids


def main():
    """Entry point: authenticate, search records via Lucene query, validate and generate reports."""
    setup_logging(debug=False)  # ← Disable DEBUG

    # === CONFIGURATION ===
    API_URL = config.API_URL
    USERNAME = config.GEOCAT_USERNAME
    PASSWORD = config.GEOCAT_PASSWORD

    if not USERNAME or not PASSWORD:
        logging.error("❌ Missing credentials")
        return

    logging.info(f"🌍 Environment: {config.ENVIRONMENT}")
    logging.info(f"🔗 API URL: {API_URL}")

    analyzer = GeoNetworkValidationAnalyzer(API_URL, USERNAME, PASSWORD)

    if not analyzer.authenticate():
        return

    # === RETRIEVE UUIDs via server-side Lucene/ES query ===
    search_query = config.SERVER_SEARCH_QUERY
    logging.info(f"🔎 Filter query: {json.dumps(search_query, ensure_ascii=False)}")

    uuids = analyzer.search_records(search_query, page_size=config.SEARCH_PAGE_SIZE)

    if not uuids:
        logging.error("❌ No UUIDs found with this filter")
        return

    logging.info(f"🔎 {len(uuids)} records found")

    # === VALIDATION ===
    script_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(script_dir, f"validation_reports_{config.ENVIRONMENT}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    logging.info(f"🔬 Individual validation (XSD + Schematron) via PUT /records/{{uuid}}/validate/internal")
    logging.info(f"⏳ {len(uuids)} records to validate – this may take several minutes...")

    validation_data = analyzer.validate_all_individually(uuids)

    # === REPORTS ===
    logging.info("📇 Fetching contact information...")
    contact_info = analyzer.fetch_contact_info(uuids)

    analyzer.generate_csv_report(validation_data, os.path.join(output_dir, "validation_errors.csv"), contact_info=contact_info)
    statistics = analyzer.generate_error_statistics(validation_data)
    analyzer.save_statistics_report(statistics, os.path.join(output_dir, "validation_statistics.json"))
    analyzer.generate_summary_report(statistics, os.path.join(output_dir, "validation_summary.txt"))
    analyzer.generate_error_distribution_csv(statistics, os.path.join(output_dir, "error_distribution.csv"))

    # === FINAL SUMMARY ===
    logging.info("\n" + "="*50)
    logging.info("FINAL SUMMARY")
    logging.info("="*50)
    logging.info(f"📁 Reports generated in: {output_dir}")
    logging.info(f"📈 Total records: {statistics['total_records']}")
    logging.info(f"✅ Records without errors: {statistics['records_without_errors']}")
    logging.info(f"❌ Records with errors: {statistics['records_with_errors']} ({statistics['error_rate']:.1f}%)")
    logging.info(f"⚠️ Total errors: {statistics['total_errors']}")

    if statistics['most_common_errors']:
        logging.info("\nTop 10 most frequent errors:")
        for i, (error, count) in enumerate(statistics['most_common_errors'][:10], 1):
            logging.info(f"\n{i}. [{count}x occurrences]")
            logging.info(f"   {error}")


if __name__ == "__main__":
    main()