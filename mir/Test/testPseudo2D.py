from mir.Pseudo2D import Pseudo2D
import unittest
from mir.MusicRetrieval import AudioSignal

class TestPseudo2D(unittest.TestCase):
    def setUp(self) -> None:
        self.audio = AudioSignal("../../song&samples/polyphonic.wav")
        self.pseudo = Pseudo2D(self.audio)

    def test_pseudo2D(self):
        self.assertIsInstance(self.pseudo, Pseudo2D)

    def test_show_multipitch_estimate(self):
        song, piano = self.pseudo.multipitch_estimate()
        self.pseudo.show_multipitch_estimate(piano)

    def test_show(self):
        self.pseudo.show(0.1)
