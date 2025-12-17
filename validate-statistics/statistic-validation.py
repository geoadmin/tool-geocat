import os
import requests
import json
import logging
import sys
import csv
import urllib3
from collections import Counter
from typing import List, Dict, Any
from datetime import datetime
import config

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def setup_logging(debug: bool = False):
    """Configuration du logging"""
    logging_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

class GeoNetworkValidationAnalyzer:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = (username, password)
        
        # Configuration du proxy si défini
        if config.PROXY_HTTP or config.PROXY_HTTPS:
            self.session.proxies = {
                'http': config.PROXY_HTTP,
                'https': config.PROXY_HTTPS
            }
        
        self.all_validation_data = []  # Stocke toutes les données de validation
        
    def authenticate(self) -> bool:
        """Authentification et récupération du token XSRF"""
        try:
            response = self.session.get(
                f"{self.base_url}/me",
                headers={"accept": "application/json"},
                verify=False
            )
            response.raise_for_status()
            
            xsrf_token = response.cookies.get("XSRF-TOKEN")
            if xsrf_token:
                self.session.headers.update({
                    "X-XSRF-TOKEN": xsrf_token,
                    "accept": "application/json"
                })
                logging.info("✅ Authentifié avec succès")
                return True
            else:
                logging.error("❌ Token XSRF non trouvé")
                return False
                
        except Exception as e:
            logging.error(f"❌ Échec de l'authentification: {e}")
            return False
    
    def validate_records(self, uuids: List[str]) -> List[Dict[str, Any]]:
        """
        Valide une liste de fiches métadonnées et collecte les erreurs
        
        Args:
            uuids: Liste des UUIDs à valider
        
        Returns:
            Liste des résultats de validation par fiche
        """
        results = []
        
        # Valider par lots de 50 pour éviter les timeouts
        batch_size = 50
        for i in range(0, len(uuids), batch_size):
            batch = uuids[i:i + batch_size]
            batch_results = self._validate_batch(batch)
            results.extend(batch_results)
            
            logging.info(f"📊 Lot {i//batch_size + 1}/{(len(uuids)-1)//batch_size + 1} traité")
        
        return results
    
    def _validate_batch(self, batch_uuids: List[str]) -> List[Dict[str, Any]]:
        """Valide un lot d'UUIDs"""
        validate_url = f"{self.base_url}/records/validate"
        
        try:
            # Utiliser la validation par batch
            params = {'uuids': ','.join(batch_uuids)}
            
            response = self.session.put(
                validate_url,
                params=params,
                verify=False
            )
            response.raise_for_status()
            
            validation_result = response.json()
            
            # Structure réelle de l'API GeoNetwork :
            # {
            #   "metadataErrors": {
            #     "48610900": [
            #       {"message": "(uuid) Is invalid", "uuid": "...", ...},
            #       {"message": "cvc-complex-type.4: Attribute 'id'...", "uuid": "...", ...},
            #       {"message": "cvc-complex-type.3.2.2: Attribute...", "uuid": "...", ...}
            #     ]
            #   }
            # }
            
            batch_results = []
            
            # Extraire les erreurs depuis metadataErrors
            metadata_errors = validation_result.get('metadataErrors', {})
            
            # Créer un dictionnaire uuid -> erreurs
            uuid_errors_map = {}
            
            for record_id, error_list in metadata_errors.items():
                for error_item in error_list:
                    uuid = error_item.get('uuid', '')
                    if uuid:
                        if uuid not in uuid_errors_map:
                            uuid_errors_map[uuid] = []
                        
                        # Extraire le message d'erreur
                        error_msg = error_item.get('message', 'Unknown error')
                        
                        # ✅ Ne pas ajouter le message générique "Is invalid" seul
                        # On ne garde que les messages techniques détaillés
                        if not error_msg.endswith("Is invalid"):
                            uuid_errors_map[uuid].append(error_msg)
            
            # Créer les résultats pour chaque UUID du batch
            for uuid in batch_uuids:
                if uuid in uuid_errors_map:
                    errors = uuid_errors_map[uuid]
                    batch_results.append({
                        'uuid': uuid,
                        'errors': errors,
                        'has_errors': True,
                        'error_count': len(errors)
                    })
                else:
                    # Pas d'erreurs pour cet UUID
                    batch_results.append({
                        'uuid': uuid,
                        'errors': [],
                        'has_errors': False,
                        'error_count': 0
                    })
            
            # Log du nombre d'erreurs trouvées
            num_with_errors = validation_result.get('numberOfRecordsWithErrors', 0)
            if num_with_errors > 0:
                logging.debug(f"  ⚠️ {num_with_errors} fiche(s) avec erreurs dans ce lot")
            
            return batch_results
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de la validation du batch: {e}")
            # Retourner des résultats d'erreur pour ce batch
            return [{'uuid': uuid, 'errors': [f"Erreur de validation: {str(e)}"], 
                     'has_errors': True, 'error_count': 1} for uuid in batch_uuids]
    
    def get_detailed_validation_per_record(self, uuids: List[str]) -> List[Dict[str, Any]]:
        """
        Récupère un rapport de validation détaillé pour chaque UUID individuellement
        (Méthode plus précise mais plus lente)
        """
        detailed_results = []
        
        for i, uuid in enumerate(uuids, 1):
            try:
                report_url = f"{self.base_url}/records/{uuid}/validate"
                
                response = self.session.get(
                    report_url,
                    headers={"accept": "application/json"},
                    verify=False
                )
                
                if response.status_code == 200:
                    report = response.json()
                    errors = report.get('errors', [])
                    
                    record_result = {
                        'uuid': uuid,
                        'errors': errors,
                        'has_errors': len(errors) > 0,
                        'error_count': len(errors),
                        'report': report
                    }
                    detailed_results.append(record_result)
                    
                    if len(errors) > 0:
                        logging.info(f"📄 {i}/{len(uuids)} - {uuid}: {len(errors)} erreur(s)")
                    else:
                        logging.info(f"✅ {i}/{len(uuids)} - {uuid}: Aucune erreur")
                        
                else:
                    logging.warning(f"⚠️ {i}/{len(uuids)} - Impossible d'obtenir le rapport pour {uuid}")
                    
            except Exception as e:
                logging.error(f"❌ {i}/{len(uuids)} - Erreur pour {uuid}: {e}")
        
        return detailed_results
    
    def generate_csv_report(self, validation_data: List[Dict[str, Any]], 
                          output_file: str = "validation_errors.csv"):
        """
        Génère un fichier CSV avec les erreurs par UUID
        """
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['uuid', 'error_count', 'errors_list', 'error_details']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for record in validation_data:
                uuid = record['uuid']
                errors = record.get('errors', [])
                error_count = record.get('error_count', 0)
                
                # Formatage des erreurs
                errors_list = "; ".join([str(e).replace('\n', ' ').replace('\r', '') 
                                       for e in errors[:10]])  # Limite à 10 erreurs
                error_details = json.dumps(errors, ensure_ascii=False)
                
                writer.writerow({
                    'uuid': uuid,
                    'error_count': error_count,
                    'errors_list': errors_list[:500],  # Limite la longueur
                    'error_details': error_details
                })
        
        logging.info(f"💾 Fichier CSV généré: {output_file}")
    
    def generate_error_statistics(self, validation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Génère des statistiques détaillées sur les erreurs
        """
        # Collecter toutes les erreurs
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
                    # Nettoyer et normaliser le message d'erreur
                    error_str = str(error).strip()
                    all_errors.append({
                        'uuid': record['uuid'],
                        'error': error_str
                    })
                    error_counter[error_str] += 1
        
        # Statistiques
        total_records = len(validation_data)
        records_without_errors = total_records - records_with_errors
        
        # Les erreurs les plus fréquentes
        most_common_errors = error_counter.most_common(20)
        
        # Regrouper les erreurs par pattern
        error_patterns = {}
        for error, count in error_counter.items():
            # Extraire un pattern simple (premier mot ou première phrase)
            pattern = error.split('.')[0] if '.' in error else error.split()[0] if error else "Unknown"
            if pattern not in error_patterns:
                error_patterns[pattern] = {'count': 0, 'examples': []}
            error_patterns[pattern]['count'] += count
            if len(error_patterns[pattern]['examples']) < 3:
                error_patterns[pattern]['examples'].append(error)
        
        # Trier les patterns par fréquence
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
        """Sauvegarde les statistiques dans un fichier JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, indent=2, ensure_ascii=False)
        
        logging.info(f"💾 Statistiques sauvegardées: {output_file}")
    
    def generate_summary_report(self, statistics: Dict[str, Any], 
                              output_file: str = "validation_summary.txt"):
        """Génère un rapport texte synthétique"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("RAPPORT DE VALIDATION DES MÉTADONNÉES\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Date de génération: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Environnement: {config.ENVIRONMENT}\n\n")
            
            f.write("📊 STATISTIQUES GLOBALES\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total des fiches analysées: {statistics['total_records']}\n")
            f.write(f"Fiches avec erreurs: {statistics['records_with_errors']} "
                   f"({statistics['error_rate']:.1f}%)\n")
            f.write(f"Fiches sans erreurs: {statistics['records_without_errors']}\n")
            f.write(f"Total des erreurs: {statistics['total_errors']}\n")
            f.write(f"Moyenne d'erreurs par fiche: {statistics['average_errors_per_record']:.2f}\n\n")
            
            f.write("🚨 ERREURS LES PLUS FRÉQUENTES\n")
            f.write("-" * 40 + "\n")
            for i, (error, count) in enumerate(statistics['most_common_errors'][:15], 1):
                f.write(f"{i:2d}. [{count} fiches] {error[:100]}...\n")
            
            f.write("\n🔍 PATTERNS D'ERREURS (TOP 10)\n")
            f.write("-" * 40 + "\n")
            for pattern, data in list(statistics['error_patterns'].items())[:10]:
                f.write(f"\n• {pattern}\n")
                f.write(f"  Affecte {data['count']} occurrences\n")
                f.write(f"  Exemples:\n")
                for example in data['examples'][:2]:
                    f.write(f"    - {example[:80]}...\n")
            
            f.write("\n" + "=" * 60 + "\n")
        
        logging.info(f"📝 Rapport synthétique généré: {output_file}")
    
    def generate_error_distribution_csv(self, statistics: Dict[str, Any],
                                      output_file: str = "error_distribution.csv"):
        """Génère un CSV avec la distribution des erreurs"""
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['error_message', 'occurrence_count', 'affected_records_percentage', 'example']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            total_records = statistics['total_records']
            
            for error_msg, count in statistics['most_common_errors']:
                percentage = (count / total_records) * 100 if total_records > 0 else 0
                
                writer.writerow({
                    'error_message': error_msg[:200],  # Limite la longueur
                    'occurrence_count': count,
                    'affected_records_percentage': f"{percentage:.1f}%",
                    'example': error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                })
        
        logging.info(f"📈 Distribution des erreurs CSV générée: {output_file}")

    def get_detailed_validation_report(self, uuid: str) -> Dict[str, Any]:
        """
        Récupère le rapport de validation détaillé via l'endpoint /editor
        
        Args:
            uuid: UUID de la fiche métadonnée
            
        Returns:
            Dictionnaire contenant le rapport détaillé ou None si erreur
        """
        try:
            # Endpoint de l'éditeur avec validation
            editor_url = f"{self.base_url}/records/{uuid}/editor"
            params = {'withValidationErrors': 'true'}
            
            response = self.session.post(
                editor_url,
                params=params,
                headers={"accept": "application/json"},
                verify=False
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logging.warning(f"⚠️ Validation détaillée impossible pour {uuid}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Erreur lors de la validation détaillée pour {uuid}: {e}")
            return None
    
    def extract_detailed_errors(self, validation_report: Dict[str, Any]) -> List[str]:
        """
        Extrait les erreurs détaillées depuis un rapport de validation de l'éditeur
        
        Args:
            validation_report: Rapport retourné par /editor?withValidationErrors=true
            
        Returns:
            Liste des messages d'erreur détaillés
        """
        detailed_errors = []
        
        if not validation_report:
            return detailed_errors
        
        # L'API /editor peut retourner plusieurs structures
        # Structure 1 : validation errors dans une clé spécifique
        if 'validationErrors' in validation_report:
            errors = validation_report.get('validationErrors', [])
            for error in errors:
                if isinstance(error, dict):
                    message = error.get('message', '') or error.get('error', '') or str(error)
                    xpath = error.get('xpath', '')
                    rule = error.get('rule', '')
                    
                    error_text = message
                    if xpath:
                        error_text += f" (XPath: {xpath})"
                    if rule:
                        error_text += f" [Règle: {rule}]"
                    
                    detailed_errors.append(error_text)
                else:
                    detailed_errors.append(str(error))
        
        # Structure 2 : erreurs dans 'errors' au niveau racine
        elif 'errors' in validation_report:
            errors = validation_report.get('errors', [])
            for error in errors:
                if isinstance(error, dict):
                    message = error.get('message', '') or error.get('description', '') or str(error)
                    detailed_errors.append(message)
                else:
                    detailed_errors.append(str(error))
        
        # Structure 3 : Schematron report (si présent)
        elif 'report' in validation_report:
            report = validation_report.get('report', [])
            
            # Structure: report -> patterns -> rules
            for section in report:
                patterns = section.get('patterns', {}).get('pattern', [])
                
                for pattern in patterns:
                    pattern_title = pattern.get('title', 'Unknown pattern')
                    rules = pattern.get('rules', {}).get('rule', [])
                    
                    for rule in rules:
                        rule_msg = rule.get('msg', '')
                        rule_details = rule.get('details', '')
                        rule_test = rule.get('test', '')
                        rule_type = rule.get('type', 'error')
                        
                        # Ne garder que les erreurs (pas les warnings/infos)
                        if rule_type.lower() in ['error', 'fatal']:
                            error_text = f"[{pattern_title}] {rule_msg}"
                            
                            if rule_details:
                                error_text += f" - {rule_details}"
                            
                            if rule_test:
                                error_text += f" (Test: {rule_test})"
                            
                            detailed_errors.append(error_text)
        
        # Structure 4 : Message simple dans 'validation'
        elif 'validation' in validation_report:
            validation = validation_report.get('validation', {})
            if isinstance(validation, dict):
                status = validation.get('status', '')
                messages = validation.get('messages', [])
                
                if status == 'invalid':
                    for msg in messages:
                        if isinstance(msg, dict):
                            detailed_errors.append(msg.get('message', str(msg)))
                        else:
                            detailed_errors.append(str(msg))
        
        return detailed_errors

"""    def validate_records_individually(self, uuids: List[str], fetch_detailed_errors: bool = True) -> List[Dict[str, Any]]:
        """"""
        Valide chaque UUID individuellement avec détails optionnels
        
        Args:
            uuids: Liste des UUIDs à valider
            fetch_detailed_errors: Si True, récupère les erreurs détaillées via /editor
        
        Returns:
            Liste des résultats de validation par fiche
        """"""
        results = []
        total = len(uuids)
        
        for i, uuid in enumerate(uuids, 1):
            try:
                # 1. Validation basique pour savoir si la fiche a des erreurs
                validate_url = f"{self.base_url}/records/validate"
                params = {'uuids': uuid}
                
                response = self.session.put(
                    validate_url,
                    params=params,
                    verify=False
                )
                
                # ✅ Accepter 200 ET 201 comme succès
                if response.status_code in [200, 201]:
                    validation_result = response.json()
                    
                    # Extraire les erreurs depuis metadataErrors
                    metadata_errors = validation_result.get('metadataErrors', {})
                    
                    has_errors = len(metadata_errors) > 0
                    
                    errors = []
                    
                    # Si la fiche a des erreurs ET qu'on veut les détails
                    if has_errors and fetch_detailed_errors:
                        logging.debug(f"🔍 Récupération des détails pour {uuid} via /editor")
                        
                        # 2. Récupérer le rapport détaillé via /editor
                        detailed_report = self.get_detailed_validation_report(uuid)
                        
                        if detailed_report:
                            # 🐛 DEBUG : Logger la structure complète du rapport
                            logging.debug(f"📋 Structure du rapport /editor pour {uuid}:")
                            logging.debug(json.dumps(detailed_report, indent=2, ensure_ascii=False)[:2000])
                            
                            errors = self.extract_detailed_errors(detailed_report)
                            
                            if not errors:
                                # Si aucune erreur n'a été extraite, utiliser le message basique
                                logging.warning(f"⚠️ Aucune erreur détaillée extraite pour {uuid}, utilisation du message basique")
                                for record_id, error_list in metadata_errors.items():
                                    for error_item in error_list:
                                        error_uuid = error_item.get('uuid', '')
                                        if error_uuid == uuid:
                                            error_msg = error_item.get('message', 'Unknown error')
                                            errors.append(error_msg)
                        else:
                            # Fallback sur le message basique
                            logging.warning(f"⚠️ Impossible de récupérer le rapport /editor pour {uuid}")
                            for record_id, error_list in metadata_errors.items():
                                for error_item in error_list:
                                    error_uuid = error_item.get('uuid', '')
                                    if error_uuid == uuid:
                                        error_msg = error_item.get('message', 'Unknown error')
                                        errors.append(error_msg)
                    
                    elif has_errors:
                        # Utiliser seulement le message basique
                        for record_id, error_list in metadata_errors.items():
                            for error_item in error_list:
                                error_uuid = error_item.get('uuid', '')
                                if error_uuid == uuid:
                                    error_msg = error_item.get('message', 'Unknown error')
                                    errors.append(error_msg)
                    
                    record_result = {
                        'uuid': uuid,
                        'errors': errors,
                        'has_errors': has_errors,
                        'error_count': len(errors),
                        'report': validation_result
                    }
                    results.append(record_result)
                    
                    # Log progression
                    if i % 50 == 0 or has_errors:
                        if has_errors:
                            logging.info(f"⚠️ {i}/{total} - {uuid}: {len(errors)} erreur(s)")
                        else:
                            logging.info(f"✅ {i}/{total} - Progression: {(i/total)*100:.1f}%")
                        
                else:
                    # ❌ Vraie erreur HTTP (404, 500, etc.)
                    logging.warning(f"⚠️ {i}/{total} - Status {response.status_code} pour {uuid}")
                    results.append({
                        'uuid': uuid,
                        'errors': [f"Erreur HTTP {response.status_code}"],
                        'has_errors': True,
                        'error_count': 1
                    })
                    
            except Exception as e:
                logging.error(f"❌ {i}/{total} - Erreur pour {uuid}: {e}")
                results.append({
                    'uuid': uuid,
                    'errors': [f"Exception: {str(e)}"],
                    'has_errors': True,
                    'error_count': 1
                })
        
        return results"""

def read_uuids_from_csv(filename: str = "updatedmetadata.csv") -> List[str]:
    """
    Lit les UUIDs depuis un fichier CSV contenant les métadonnées
    
    Args:
        filename: Chemin vers le fichier CSV (délimiteur virgule)
        
    Returns:
        Liste des UUIDs extraits de la colonne "Metadata ID"
    """
    uuids = []
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                metadata_id = row.get('Metadata ID', '').strip()
                
                # Vérifier que l'UUID est valide (format UUID : 36 caractères avec tirets)
                if metadata_id and len(metadata_id) == 36 and metadata_id.count('-') == 4:
                    uuids.append(metadata_id)
                elif metadata_id:
                    logging.warning(f"⚠️ UUID invalide ignoré: {metadata_id}")
        
        logging.info(f"✅ {len(uuids)} UUIDs chargés depuis {filename}")
        
    except FileNotFoundError:
        logging.error(f"❌ Fichier {filename} non trouvé")
    except Exception as e:
        logging.error(f"❌ Erreur lors de la lecture du fichier CSV: {e}")
    
    return uuids

def main():
    """Exemple d'utilisation complet"""
    setup_logging(debug=False)  # ← Désactiver le DEBUG
    
    # === CONFIGURATION ===
    API_URL = config.API_URL
    USERNAME = config.GEOCAT_USERNAME
    PASSWORD = config.GEOCAT_PASSWORD
    
    if not USERNAME or not PASSWORD:
        logging.error("❌ Identifiants manquants")
        return
    
    logging.info(f"🌍 Environnement: {config.ENVIRONMENT}")
    logging.info(f"🔗 API URL: {API_URL}")
    
    # === CHARGEMENT DES UUIDs ===
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "updatedmetadata.csv")
    
    logging.info(f"📂 Chemin du fichier CSV: {csv_path}")
    
    uuids_to_validate = read_uuids_from_csv(csv_path)
    
    if not uuids_to_validate:
        logging.error("❌ Aucun UUID à valider")
        return
    
    logging.info(f"🔍 {len(uuids_to_validate)} UUIDs à valider")
    
    # Initialiser l'analyseur
    analyzer = GeoNetworkValidationAnalyzer(API_URL, USERNAME, PASSWORD)
    
    # Authentification
    if not analyzer.authenticate():
        return
    
    # === VALIDATION PAR BATCH (RAPIDE ET COMPLET) ===
    logging.info("\n" + "="*50)
    logging.info("VALIDATION PAR BATCH")
    logging.info("="*50)
    
    # Validation par batch : rapide et retourne tous les messages d'erreur
    validation_data = analyzer.validate_records(uuids_to_validate)
    
    if not validation_data:
        logging.error("❌ Aucune donnée de validation collectée")
        return
    
    logging.info(f"✅ {len(validation_data)} fiches validées")
    
    # === GÉNÉRATION DES RAPPORTS ===
    logging.info("\n" + "="*50)
    logging.info("GÉNÉRATION DES RAPPORTS")
    logging.info("="*50)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(script_dir, f"validation_reports_{config.ENVIRONMENT}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    analyzer.generate_csv_report(validation_data, 
                                 os.path.join(output_dir, "validation_errors.csv"))
    
    statistics = analyzer.generate_error_statistics(validation_data)
    
    analyzer.save_statistics_report(statistics, 
                                   os.path.join(output_dir, "validation_statistics.json"))
    
    analyzer.generate_summary_report(statistics, 
                                    os.path.join(output_dir, "validation_summary.txt"))
    
    analyzer.generate_error_distribution_csv(statistics, 
                                            os.path.join(output_dir, "error_distribution.csv"))
    
    # === RÉSUMÉ FINAL ===
    logging.info("\n" + "="*50)
    logging.info("RÉSUMÉ FINAL")
    logging.info("="*50)
    logging.info(f"📁 Rapports générés dans: {output_dir}")
    logging.info(f"📈 Total fiches: {statistics['total_records']}")
    logging.info(f"✅ Fiches sans erreurs: {statistics['records_without_errors']}")
    logging.info(f"❌ Fiches avec erreurs: {statistics['records_with_errors']} "
                f"({statistics['error_rate']:.1f}%)")
    logging.info(f"⚠️ Total erreurs: {statistics['total_errors']}")
    
    if statistics['most_common_errors']:
        logging.info("\nTop 10 des erreurs les plus fréquentes:")
        for i, (error, count) in enumerate(statistics['most_common_errors'][:10], 1):
            # Afficher le message complet (pas tronqué)
            logging.info(f"\n{i}. [{count}x occurrences]")
            logging.info(f"   {error}")


if __name__ == "__main__":
    main()