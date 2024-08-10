#!/usr/bin/env python3
"""Create a recording with arbitrary duration.

The soundfile module (https://python-soundfile.readthedocs.io/)
has to be installed!

"""
import argparse
import tempfile
import queue
import sys
import threading
import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

stop = threading.Event()
device_info = sd.query_devices()

class Args:
    def __init__(self):
        self.filename = None
        self.device = 0
        self.samplerate = 44100
        self.channels = 1
    def __repr__(self) -> str:
        return f"Args(filename={self.filename}, device={self.device}, samplerate={self.samplerate}, channels={self.channels})"
args = Args()
q = queue.Queue()

print(args)
def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())

def user_input():
    input("")
    stop.set()
def record():

    try:
        print("choose a device:")
        print(sd.query_devices())
        device = int(input())
        print("you chose: ", device)
        threading.Thread(target=user_input).start()
        f = tempfile.mktemp(prefix='delme_rec_unlimited_',
                                                suffix='.wav', dir='output')
        if args.samplerate is None:
            device_info = sd.query_devices(args.device, 'input')
            # soundfile expects an int, sounddevice provides a float:
            args.samplerate = int(device_info['default_samplerate'])

        # Make sure the file is opened before recording anything:
        with sf.SoundFile(f, mode='x', samplerate=args.samplerate,
                        channels=args.channels, subtype=None) as file:
            with sd.InputStream(samplerate=args.samplerate, device=device,
                                channels=args.channels, callback=callback):
                print('Press Enter to stop the recording')
                while not stop.is_set():
                    file.write(q.get())
        return f
    except KeyboardInterrupt:
        print('\nRecording finished: ' + repr(args.filename))
        return f

    except Exception as e:
        exit(type(e).__name__ + ': ' + str(e))
