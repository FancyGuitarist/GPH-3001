#!/bin/bash

# Main script

# Vérifiez que le nom de fichier est fourni
if [ $# -ne 1 ]; then
    echo "Usage: $0  <audiofile.wav>"
    exit 1
fi
# Vérifiez que le venv est activé
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment is already activated."
else
    if [ -d "venv" ]; then
        echo "Activating virtual environment..."
        source ./venv/bin/activate
    else
        echo "Error: Virtual environment directory 'venv' not found."
        sh setup.sh
        exit 1
    fi
fi


# Variables
PYTHON_SCRIPT="main.py"
AUDIO_FILE="$1"

python "$PYTHON_SCRIPT" "$AUDIO_FILE"
name=$(basename "$AUDIO_FILE" .wav)

lilypond --output="./output/$name" "$name".ly &> /dev/null

open "./output/$name".pdf
