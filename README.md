# instruction
```
sh setup.sh
```
```
source venv/bin/activate
```
```
python main.py -h
```

## exemple d'utilisation
*Roule les test de performance de l'analyse polyphonic sur le dataset MAESTRO*
```
python main.py polyphonic -b Validation/polyphonic_piano_test.midi
```
*Analyse Monophonic d'un enregistrement préexistant*
```
python main.py monophonic -f /Users/antoine/Desktop/GPH/E2024/PFE/song&samples/gamme_C.wav
```
