# OGC Services Checker

Ce projet Python permet de vérifier les services OGC (WMS, WMTS, WFS) en s'appuyant sur des capacités GetCapabilities.  
Il inclut des scripts pour :
- Vérifier la validité des URLs.
- Vérifier la présence de couches spécifiques dans les réponses XML.

## Structure du projet
- `config.py` : Configuration du projet.
- `main.py` : Script principal.
- `ogc_service_checker.py` : Script pour vérifier les services OGC.

## Installation
1. Cloner le dépôt.
2. Installer les dépendances avec `pip install -r requirements.txt`.

## Utilisation
Exécuter le script principal :
```bash
python main.py
