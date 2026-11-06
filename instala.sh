#!/usr/bin/env bash
# Copia o Trava pro addons21 do Anki (flatpak) e gera o trava.ankiaddon.
# O flatpak não enxerga ~/deving, por isso cópia e não symlink.
# config.local.json (se existir) vira o config.json instalado; o .ankiaddon leva o padrão.
# Reinicie o Anki depois.
set -euo pipefail
cd "$(dirname "$0")"

ARQS=(__init__.py regras.py config.json config.md manifest.json)
DEST="$HOME/.var/app/net.ankiweb.Anki/data/Anki2/addons21/trava"

./trava_test.sh >/dev/null 2>&1 || { ./trava_test.sh; exit 1; }

mkdir -p "$DEST"
cp "${ARQS[@]}" "$DEST/"
[ -f config.local.json ] && cp config.local.json "$DEST/config.json"
rm -rf "$DEST/__pycache__"
echo "instalado em $DEST"

rm -f trava.ankiaddon
python3 -I -c 'import sys, zipfile
with zipfile.ZipFile("trava.ankiaddon", "w", zipfile.ZIP_DEFLATED) as z:
    for a in sys.argv[1:]: z.write(a)' "${ARQS[@]}"
echo "pacote: $PWD/trava.ankiaddon (Ferramentas › Complementos › Instalar do arquivo)"
