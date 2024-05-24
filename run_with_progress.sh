#!/bin/bash
# Function to check if the venv is activated
is_venv_activated() {
    [[ "$VIRTUAL_ENV" != "" ]]
}

# Function to activate the venv
activate_venv() {
    source venv/bin/activate
}

# Main script
if is_venv_activated; then
    echo "Virtual environment is already activated."
else
    if [ -d "venv" ]; then
        echo "Activating virtual environment..."
        activate_venv
    else
        echo "Error: Virtual environment directory 'venv' not found."
        exit 1
    fi
fi
# Vérifiez que le nom de fichier est fourni
if [ $# -ne 1 ]; then
    echo "Usage: $0 <python_script>"
    exit 1
fi

# Variables
PYTHON_SCRIPT="$1"
TMP_FILE=$(mktemp)
PROGRESS_INDICATOR="-----------"
PROGRESS_LENGTH=${#PROGRESS_INDICATOR}
INTERVAL=0.1

# Fonction pour afficher la barre de progression
show_progress() {
    local progress=0
    while [ $progress -lt $PROGRESS_LENGTH ]; do
        echo -ne "\rProgress: [${PROGRESS_INDICATOR:0:$progress}>]"
        progress=$((progress + 1))
        sleep $INTERVAL
    done
}

# Démarrer le script Python dans un sous-processus
python3 "$PYTHON_SCRIPT" &> "$TMP_FILE" &

# Appeler la fonction de barre de progression
show_progress

# Afficher la sortie du script Python après l'exécution complète
# cat "$TMP_FILE"
./compile_with_progress.sh output_score.ly
# Nettoyer le fichier temporaire
rm "$TMP_FILE"
open output_score.pdf
