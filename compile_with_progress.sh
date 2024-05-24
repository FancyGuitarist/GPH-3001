#!/bin/bash

# Vérifiez que le nom de fichier est fourni
if [ $# -ne 1 ]; then
    echo "Usage: $0 <file.ly>"
    exit 1
fi

# Variables
LY_FILE="$1"
TMP_FILE=$(mktemp)
COMPILE_LOG="compile.log"

# Fonction pour afficher la barre de progression
show_progress() {
    local progress=0
    local max_progress=10
    local increment=2
    local completed=0

    while IFS= read -r line; do
        if [[ $line == *"processing"* ]]; then
            completed=$((completed + 1))
            progress=$((completed * increment))
            echo -ne "\rProgress: ["
            for ((i = 0; i < progress; i++)); do echo -n "#"; done
            for ((i = progress; i < max_progress; i++)); do echo -n "."; done
            echo -n "]"
        fi
    done < "$TMP_FILE"
    echo -e "\nCompilation completed!"
}

# Démarrer la compilation dans un sous-processus
lilypond "$LY_FILE" &> "$TMP_FILE" &

# Appeler la fonction de barre de progression
show_progress

# Nettoyer le fichier temporaire
rm "$TMP_FILE"

