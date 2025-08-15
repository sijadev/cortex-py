#!/bin/bash
# Weekly Deep Check für Cortex System
# Umfassende Validierung und Optimierung

echo "🔍 Cortex Weekly Deep Check - $(date)"
echo "============================================"

# Wechsle ins Cortex-Verzeichnis
cd /Users/simonjanke/Projects/cortex-py

# 1. Umfassende Datenvalidierung
echo "📊 1. Validiere Datenstrukturen..."
python cortex_neo/cortex_cli.py validate-graph

# 2. Link-Validierung mit AI
echo "🤖 2. AI-Link-Validierung..."
python cortex_neo/cortex_cli.py link-validate-ai

# 3. Verwaiste Knoten finden
echo "🏝️ 3. Suche verwaiste Knoten..."
python cortex_neo/cortex_cli.py validate-graph | grep -E "(orphan|verwaist)"

# 4. Backup-Integrität prüfen
echo "💾 4. Prüfe Backup-Integrität..."
BACKUP_COUNT=$(find cortex_neo/backups -name "*.yaml" -mtime -7 | wc -l)
echo "   📦 Backups letzte 7 Tage: $BACKUP_COUNT"

if [ $BACKUP_COUNT -lt 3 ]; then
    echo "   ⚠️ Warnung: Zu wenige Backups!"
fi

# 5. Log-Dateien rotieren
echo "📜 5. Rotiere Log-Dateien..."
mkdir -p logs/archive
find logs -name "*.log" -mtime +30 -exec mv {} logs/archive/ \;

# 6. Performance-Statistiken
echo "⚡ 6. Performance-Check..."
NOTES_COUNT=$(python cortex_neo/cortex_cli.py validate-graph | grep -o '"notes": [0-9]*' | grep -o '[0-9]*')
LINKS_COUNT=$(python cortex_neo/cortex_cli.py validate-graph | grep -o '"links": [0-9]*' | grep -o '[0-9]*')

echo "   📊 Notes: $NOTES_COUNT"
echo "   🔗 Links: $LINKS_COUNT"

# Link-Dichte berechnen
if [ $NOTES_COUNT -gt 0 ]; then
    LINK_DENSITY=$(echo "scale=2; $LINKS_COUNT / $NOTES_COUNT" | bc -l)
    echo "   📈 Link-Dichte: $LINK_DENSITY Links/Note"
    
    # Warnung bei niedriger Link-Dichte
    LOW_DENSITY=$(echo "$LINK_DENSITY < 1.5" | bc -l)
    if [ $LOW_DENSITY -eq 1 ]; then
        echo "   ⚠️ Niedrige Link-Dichte! Mehr Verlinkung empfohlen."
    fi
fi

# 7. Automatische Optimierungen (optional)
echo "🔧 7. Automatische Optimierungen..."

# Nur wenn explizit gewünscht (auskommentiert für Sicherheit)
# echo "   🔄 Auto-Link-Generierung..."
# python cortex_neo/cortex_cli.py auto-link-by-content --min-similarity 0.2

# 8. Abschlussbericht
echo "✅ Weekly Deep Check abgeschlossen - $(date)"
echo "============================================"

# Optional: E-Mail-Bericht senden (wenn mailx installiert)
# echo "Deep Check Report attached" | mail -s "Cortex Weekly Report" your-email@domain.com
