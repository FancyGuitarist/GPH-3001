#!/bin/bash
# Function to check if the venv is activated

is_venv_activated() {
    [[ "$VIRTUAL_ENV" != "" ]]
}

# Function to activate the venv
activate_venv() {
    source ./venv/bin/activate
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
if [ $# -ne 2 ]; then
    echo "Usage: $0 <python_script> <audiofile.wav>"
    exit 1
fi

# Variables
PYTHON_SCRIPT="$1"
AUDIO_FILE="$2"
TMP_FILE=$(mktemp)

# Démarrer le script Python dans un sous-processus
python "$PYTHON_SCRIPT" "$AUDIO_FILE" &> "$TMP_FILE"
name=$(basename "$AUDIO_FILE" .wav)
# Appeler la fonction de barre de progression
# Afficher la sortie du script Python après l'exécution complète
# cat "$TMP_FILE"
echo "$name.ly"
lilypond "$name".ly &> /dev/null
# Nettoyer le fichier temporaire
open "$name".pdf
rm "$TMP_FILE"
