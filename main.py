from MusicRetrieval import AudioSignal, CustomHMM, Prior, Postprocessor
import numpy as np
import sys





if __name__ == '__main__':
    name = sys.argv[1].split("/")[-1].split(".")[0]
    output_path = f"{name}.ly"
    audio_path = sys.argv[1]

    import librosa
    audio = AudioSignal(audio_path)
    prior = Prior(audio.y_harmonic,audio.y_percussive)
    hmm = CustomHMM(prior)
    pitch , flag, prob = prior.pyin()
    p = Postprocessor(hmm)
    simple_notation = p.simple_notation

    from anotation import Partition
    partition = Partition(simple_notation, audio.tempo)

    partition.save_score(output_path)
