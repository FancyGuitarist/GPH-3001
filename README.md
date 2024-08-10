# instruction
```
sh setup.sh
```
```
source venv/bin/activate
```
```
python mir --help
```

## exemple d'utilisation
*Roule les test de performance de l'analyse polyphonic sur le dataset MAESTRO*
```
python mir polyphonic -b mir/Validation/polyphonic_piano_test.midi
```
*Analyse Monophonic d'un enregistrement préexistant*
```
python mir monophonic -f /Users/antoine/Desktop/GPH/E2024/PFE/song&samples/gamme_C.wav
```

*identification des accords d'un enregistrement préexistant*
```
python mir chord-only -f -pr /Users/antoine/Desktop/GPH/E2024/PFE/song&samples/polyphonic.wav
```
