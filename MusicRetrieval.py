import librosa as lb
from numpy.random.mtrand import sample
import scipy.io.wavfile as wav
import numpy as np
import matplotlib.pyplot as plt

#test = "/Users/antoine/Desktop/GPH/E2024/PFE/80bpm.wav"
audiopath = './song&samples/Chopin_fantaisy_impromptu.wav'
#samples, sr = load(test)
#chroma = chroma_stft(y=samples,sr=sr)


# break musical note in their time fraction
# insert them in a sheet
class MRI:
    notes = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    def __init__(self,audio_path) -> None:
        self.audio_path = audio_path
        self.sample, self.sample_rate = lb.load(audio_path)
        self.short_ft = lb.stft(self.sample)
        self.harmonic, self.percussive = lb.decompose.hpss(self.short_ft)
        self.time_harmonic = lb.istft(self.harmonic)
        self.time_percussive = lb.istft(self.percussive)
        self.tempo, self.beat = lb.beat.beat_track(y=self.time_percussive, sr=self.sample_rate)
        self.ratio = lb.feature.tempogram_ratio(y=self.time_percussive, sr=self.sample_rate, bpm=self.tempo.item())


def transition_matrix()





if __name__ == "__main__":
    pass
