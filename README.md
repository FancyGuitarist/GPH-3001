
# Instructions

1. **Set up the environment**:
   ```bash
   sh setup.sh
   ```

2. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

3. **Check available commands**:
   ```bash
   python -m mir --help
   ```

## Example Usage

### Run performance tests for polyphonic analysis on the MAESTRO dataset
```bash
python -m mir polyphonic -b mir/Validation/polyphonic_piano_test.midi
```

### Perform monophonic analysis on a pre-existing recording
```bash
python -m mir monophonic -f song&samples/gamme_C.wav
```

### Identify chords in a pre-existing recording and show the piano roll
```bash
python -m mir chord-only -pr -f song&samples/polyphonic.wav
```

### Perform monophonic analysis on a single instrument in a pre-existing recording
```bash
python -m mir monophonic --extract guitar -f /path/to/song.wav
```
