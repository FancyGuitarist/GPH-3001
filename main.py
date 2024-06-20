from MusicRetrieval import AudioSignal, CustomHMM, Preprocessor, Postprocessor
from MIR_lib import build_transition_matrix
import numpy as np
import sys





if __name__ == '__main__':
    name = sys.argv[1].split("/")[-1].split(".")[0]
    output_path = f"{name}.ly"
    audio_path = sys.argv[1]

    audio = AudioSignal(audio_path)
    priors = Preprocessor(audio.y_harmonic,audio.y_percussive).priors
    hmm = CustomHMM(priors, build_transition_matrix(n_notes=audio.n_notes))
    p = Postprocessor(hmm.resolved_states())
    simple_notation = p.simple_notation

    from anotation import Partition
    partition = Partition(simple_notation, audio.tempo)

    partition.save_score(output_path)
