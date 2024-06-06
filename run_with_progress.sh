#!/bin/bash
# Function to check if the venv is activated
# Vérifier si Brew est installé
if ! command -v brew &> /dev/null
then
    echo "Homebrew n'est pas installé. Veuillez installer Homebrew d'ab
ord : https://brew.sh/"
    exit 1
fi

# Vérifier si LilyPond est installé
if brew list | grep  "^lilypond$" &> /dev/null ; then
    echo "LilyPond est déjà installé."
else
    echo "LilyPond n'est pas installé. Installation en cours..."
    brew install lilypond
    if [ $? -eq 0 ]; then
        echo "LilyPond a été installé avec succès."
    else
        echo "L'installation de LilyPond a échoué."
    fi
fi
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
