#!/bin/bash

verify_installation () {
# Vérifier si Brew est installé
if ! command -v brew &> /dev/null
then
    echo "Homebrew n'est pas installé. Veuillez installer Homebrew d'ab
ord : https://brew.sh/"
    exit 1
fi
# Vérifier si ffmpeg est installé
if brew list | grep  "^ffmpeg$" &> /dev/null ; then
    echo "ffmpeg est déjà installé."
else
    echo "ffmpeg n'est pas installé. Installation en cours..."
    brew install ffmpeg
    if [ $? -eq 0 ]; then
        echo "ffmpeg a été installé avec succès."
    else
        echo "L'installation de ffmpeg a échoué."
    fi
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

if brew list | grep "^virtualenv$"; then
    echo "virtualenv est déjà installé."
else
    echo "virtualenv n'est pas installé. Veuiller l'installer.\n  brew install virtualenv"
        exit 1
       if [ $? -eq 0 ]; then
        echo "virtualenv a été installé avec succès."
    else
        echo "L'installation de virtualenv a échoué."
    fi
fi

}
function complete_setup {
virtualenv --python=3.11  venv
source ./venv/bin/activate
pip install -r requirements.txt
chmod +x start.sh
chmod +x run_with_progress.sh
}
complete_setup
if [ $? -eq 0 ]; then
    echo "Prérequis complété, vous pouvez désormais executer ./start.sh"
else
    "setup.sh à échoué"
fi
