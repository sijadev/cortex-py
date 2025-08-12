#!/bin/bash

# Erstelle temporäre Dateien
ALL_FILES="/tmp/all_python_files.txt"
IMPORTED_MODULES="/tmp/imported_modules.txt"
UNUSED_FILES="/tmp/unused_files.txt"

# Lösche alte Ergebnisse
> $IMPORTED_MODULES
> $UNUSED_FILES

# Finde alle Python-Dateien im Projekt und speichere sie in ALL_FILES
find /workspaces/cortex-py/cortex -name "*.py" | sort > $ALL_FILES

# Finde alle Python-Importe im Projekt
grep -r "^from cortex\." --include="*.py" /workspaces/cortex-py/cortex | \
  sed -E 's/.*from (cortex[^ ]*).*/\1/g' | sort | uniq > $IMPORTED_MODULES
grep -r "^import cortex\." --include="*.py" /workspaces/cortex-py/cortex | \
  sed -E 's/.*import (cortex[^ ]*).*/\1/g' | sort | uniq >> $IMPORTED_MODULES

# Vergleiche alle Dateien mit den tatsächlich importierten
while read -r file; do
  # Konvertiere Dateipfad in Modulpfad
  module=$(echo $file | sed 's/\/workspaces\/cortex-py\///' | sed 's/\.py$//' | sed 's/\//./g')
  
  # Prüfe, ob das Modul in irgendeiner anderen Datei importiert wird
  if ! grep -q "$module" $IMPORTED_MODULES; then
    # Prüfe, ob die Datei eine ausführbare Datei (Entry Point) ist
    if ! grep -q "if __name__ == .__main__." "$file"; then
      echo "$file" >> $UNUSED_FILES
    fi
  fi
done < $ALL_FILES

# Ausgabe der Ergebnisse
echo "Möglicherweise ungenutzte Dateien:"
cat $UNUSED_FILES

# Lösche die temporären Dateien
rm -f $ALL_FILES $IMPORTED_MODULES $UNUSED_FILES
echo "Temporäre Ergebnislisten wurden gelöscht."