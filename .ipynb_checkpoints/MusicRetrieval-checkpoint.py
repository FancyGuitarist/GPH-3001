from librosa.feature import chroma_stft
from librosa.display import specshow
from librosa import load, stft, decompose
from numpy.random.mtrand import sample
import scipy.io.wavfile as wav
from librosa.beat import beat_track
import numpy as np
import matplotlib.pyplot as plt

#test = "/Users/antoine/Desktop/GPH/E2024/PFE/80bpm.wav"
audiopath = 'Chopin_fantaisy_impromptu.wav'
#samples, sr = load(test)
#chroma = chroma_stft(y=samples,sr=sr)


# break musical note in their time fraction
# insert them in a sheet
class MRI:
    def __init__(self,audio_path) -> None:
        self.audio_path = audio_path
        self.samples, self.sample_rate = load(audio_path)
    @property
    def bpm(self):
        return beat_track(y=self.samples, sr=self.sample_rate)[0].mean()
    @property
    def _chroma(self):
        D = stft(self.samples)
        harmonic, percusive = decompose.hpss(D)
        return chroma_stft(y=self.samples,sr=self.sample_rate)
    def _decompose_into(self):
        # decompose tune into a 1/32th note interval based on tempo
        time, freq = self._chroma



if __name__ == "__main__":
    m = MRI(audiopath)
    print(m.bpm)
