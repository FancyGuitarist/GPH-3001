#!/bin/bash
if [ $# -ne 1 ]; then
    echo "Usage: $0 </path/to/audiofile.wav>"
    exit 1
fi


./run_with_progress.sh Monophonic.py $1
