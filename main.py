from MusicRetrieval import AudioSignal, Mono
from Chord import ChordIdentifier
import numpy as np
import sys
from bivariate import Pseudo2D




if __name__ == '__main__':
    name = sys.argv[1].split("/")[-1].split(".")[0]
    output_path = f"{name}.ly"
    audio_path = sys.argv[1]

    audio = AudioSignal(audio_path)
    mono = Mono(audio.y_harmonic, audio.y_percussive)
    pseudo2d = Pseudo2D(audio)
    #mono.simple_notation
    from anotation import Partition
    partition = Partition(mono.simple_notation, audio.tempo)

    partition.save_score(output_path)
