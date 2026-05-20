#!/usr/bin/env python3
"""
analyze_mandatory_only.py
--------------------------
Relit un dossier validation_reports existant, filtre les erreurs non-bloquantes
(recommended rules et URL Validation) et régénère tous les rapports dans un
nouveau dossier suffixé _mandatory_only.

Règles filtrées (non-obligatoires dans la config actuelle) :
  - [BGDI-SWISSGEO - recommended rules] ...
  - [URL Validation] ...

Usage:
    python analyze_mandatory_only.py [chemin_dossier_rapports]

Si aucun chemin n'est fourni, le dossier validation_reports_* le plus récent
est utilisé automatiquement.
"""

import ast
import csv
import glob
import importlib.util
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional


# ── Patterns d'erreurs NON-obligatoires à exclure ────────────────────────────

EXCLUDED_PREFIXES = [
    "[BGDI-SWISSGEO - recommended rules]",
    "[URL Validation]",
]


def is_mandatory_error(error_msg: str) -> bool:
    """Retourne True si l'erreur est obligatoire (à conserver)."""
    return not any(error_msg.lstrip().startswith(p) for p in EXCLUDED_PREFIXES)


# ── Chargement du module principal ───────────────────────────────────────────

def _load_main_module():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mod_path = os.path.join(script_dir, "statistic-validation.py")
    spec = importlib.util.spec_from_file_location("statistic_validation", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Détection du dossier le plus récent ──────────────────────────────────────

def find_latest_reports_dir(script_dir: str) -> Optional[str]:
    pattern = os.path.join(script_dir, "validation_reports_*")
    dirs = [
        d for d in sorted(glob.glob(pattern), reverse=True)
        if os.path.isdir(d) and not d.endswith("_mandatory_only")
    ]
    return dirs[0] if dirs else None


# ── Lecture du CSV ────────────────────────────────────────────────────────────

def read_validation_data_from_csv(csv_path: str) -> tuple[List[Dict[str, Any]], Dict[str, Dict[str, str]]]:
    """
    Relit un validation_errors.csv.
    Retourne (validation_data, contact_info).
    """
    data = []
    contact_info: Dict[str, Dict[str, str]] = {}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uuid = row["uuid"].strip()

            raw_details = row.get("error_details", "[]").strip()
            try:
                errors = json.loads(raw_details)
            except (json.JSONDecodeError, ValueError):
                try:
                    errors = ast.literal_eval(raw_details)
                except Exception:
                    errors = []

            if not isinstance(errors, list):
                errors = [str(errors)] if errors else []

            data.append({
                "uuid": uuid,
                "errors": errors,
                "has_errors": len(errors) > 0,
                "error_count": len(errors),
            })

            # Conserver les infos de contact déjà présentes dans le CSV
            org = row.get("organisation", "").strip()
            email = row.get("email", "").strip()
            if org or email:
                contact_info[uuid] = {"organisation": org, "email": email}

    return data, contact_info


# ── Filtrage des erreurs non-obligatoires ────────────────────────────────────

def filter_mandatory_errors(
    validation_data: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], int, int]:
    """
    Filtre les erreurs non-obligatoires dans chaque fiche.
    Retourne (filtered_data, nb_erreurs_supprimées, nb_fiches_modifiées).
    """
    filtered_data = []
    total_removed = 0
    records_changed = 0

    for record in validation_data:
        original_errors = record["errors"]
        kept_errors = [e for e in original_errors if is_mandatory_error(e)]
        removed = len(original_errors) - len(kept_errors)

        if removed > 0:
            total_removed += removed
            records_changed += 1

        filtered_data.append({
            "uuid": record["uuid"],
            "errors": kept_errors,
            "has_errors": len(kept_errors) > 0,
            "error_count": len(kept_errors),
        })

    return filtered_data, total_removed, records_changed


# ── Point d'entrée ────────────────────────────────────────────────────────────

def main():
    mod = _load_main_module()
    mod.setup_logging(debug=False)

    import config  # noqa: E402

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # ── Dossier source ────────────────────────────────────────────────────────
    if len(sys.argv) > 1:
        source_dir = sys.argv[1]
    else:
        source_dir = find_latest_reports_dir(script_dir)
        if not source_dir:
            logging.error("❌ Aucun dossier validation_reports_* trouvé.")
            sys.exit(1)
        logging.info(f"📂 Dossier source auto-détecté : {source_dir}")

    source_csv = os.path.join(source_dir, "validation_errors.csv")
    if not os.path.exists(source_csv):
        logging.error(f"❌ Fichier introuvable : {source_csv}")
        sys.exit(1)

    # ── Lecture ───────────────────────────────────────────────────────────────
    logging.info(f"📖 Lecture des résultats depuis : {source_csv}")
    validation_data, contact_info = read_validation_data_from_csv(source_csv)
    logging.info(f"   → {len(validation_data)} fiches chargées")
    logging.info(f"   → {len(contact_info)} fiches avec info de contact")

    # ── Filtrage ──────────────────────────────────────────────────────────────
    logging.info("\n" + "=" * 50)
    logging.info("FILTRAGE DES RÈGLES NON-OBLIGATOIRES")
    logging.info("=" * 50)
    logging.info("Règles exclues des statistiques :")
    for p in EXCLUDED_PREFIXES:
        logging.info(f"  • {p}")

    filtered_data, total_removed, records_changed = filter_mandatory_errors(validation_data)

    logging.info(
        f"\n✂️  {total_removed} erreur(s) non-obligatoire(s) supprimée(s) "
        f"sur {records_changed} fiche(s)"
    )

    # Résumé avant/après
    orig_with_errors = sum(1 for r in validation_data if r["has_errors"])
    filt_with_errors = sum(1 for r in filtered_data if r["has_errors"])
    newly_valid = orig_with_errors - filt_with_errors
    logging.info(
        f"📊 Fiches avec erreurs : {orig_with_errors} → {filt_with_errors} "
        f"({newly_valid} fiches deviennent valides après filtrage)"
    )

    # ── Initialiser l'analyseur (pour les méthodes de génération de rapports) ─
    USERNAME = config.GEOCAT_USERNAME
    PASSWORD = config.GEOCAT_PASSWORD
    if not USERNAME or not PASSWORD:
        logging.error("❌ Identifiants manquants (vérifier .env)")
        sys.exit(1)

    analyzer = mod.GeoNetworkValidationAnalyzer(config.API_URL, USERNAME, PASSWORD)
    # Pas besoin d'authentification pour générer les rapports

    # ── Dossier de sortie ─────────────────────────────────────────────────────
    # Dériver le nom depuis le dossier source pour traçabilité
    source_basename = os.path.basename(source_dir.rstrip("/\\"))
    output_dir = os.path.join(script_dir, f"{source_basename}_mandatory_only")
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"\n📁 Dossier de sortie : {output_dir}")

    # ── Génération des rapports ───────────────────────────────────────────────
    logging.info("\n" + "=" * 50)
    logging.info("GÉNÉRATION DES RAPPORTS (règles obligatoires uniquement)")
    logging.info("=" * 50)

    analyzer.generate_csv_report(
        filtered_data,
        os.path.join(output_dir, "validation_errors.csv"),
        contact_info=contact_info,
    )

    statistics = analyzer.generate_error_statistics(filtered_data)
    analyzer.save_statistics_report(
        statistics, os.path.join(output_dir, "validation_statistics.json")
    )
    analyzer.generate_summary_report(
        statistics, os.path.join(output_dir, "validation_summary.txt")
    )
    analyzer.generate_error_distribution_csv(
        statistics, os.path.join(output_dir, "error_distribution.csv")
    )

    # ── Résumé final ──────────────────────────────────────────────────────────
    logging.info("\n" + "=" * 50)
    logging.info("RÉSUMÉ FINAL — Règles obligatoires uniquement")
    logging.info("=" * 50)
    logging.info(f"📁 Rapports générés dans : {output_dir}")
    logging.info(f"📈 Total fiches           : {statistics['total_records']}")
    logging.info(f"✅ Sans erreurs           : {statistics['records_without_errors']}")
    logging.info(
        f"❌ Avec erreurs          : {statistics['records_with_errors']} "
        f"({statistics['error_rate']:.1f}%)"
    )
    logging.info(f"⚠️  Total erreurs          : {statistics['total_errors']}")
    logging.info(
        f"\n🔕 Rappel : {total_removed} erreur(s) non-obligatoire(s) exclues "
        f"([URL Validation] + [recommended rules])"
    )

    if statistics["most_common_errors"]:
        logging.info("\nTop 10 des erreurs obligatoires les plus fréquentes :")
        for i, (error, count) in enumerate(statistics["most_common_errors"][:10], 1):
            short = error[:120] + "..." if len(error) > 120 else error
            logging.info(f"  {i:2d}. [{count}×] {short}")


if __name__ == "__main__":
    main()
