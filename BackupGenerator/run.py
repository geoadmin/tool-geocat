import geocat_backup

BACKUP_DIR = "M:/Appl/DATA/PROD/kogis/igeb/geocat/Metadatenapplikation geocat.ch entwickeln und betreiben (463)/" \
             "Software geocat.ch entwickeln/Betrieb Applikation geocat.ch/XML Backup/YYYYMMDD_int"

geocat_backup.GeocatBackup(backup_dir=BACKUP_DIR, env='int', catalogue=True, users=True, groups=True,
                           reusable_objects=True, thesaurus=True)
