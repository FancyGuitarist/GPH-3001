#!/bin/bash
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
