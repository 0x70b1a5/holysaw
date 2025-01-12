import numpy as np
import sounddevice as sd
import wave
from typing import Optional

class AudioEngine:
    def __init__(self, sample_rate=44100, buffer_size=2048, fade_samples=500):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.fade_samples = fade_samples
        self.stream: Optional[sd.OutputStream] = None

    def crossfade(self, s1: np.ndarray, s2: np.ndarray) -> np.ndarray:
        fade_len = min(len(s1), len(s2), self.fade_samples)
        fade = np.linspace(0, 1, fade_len)
        result = np.empty(len(s1), dtype=np.float32)
        result[:-fade_len] = s1[:-fade_len]
        result[-fade_len:] = (s1[-fade_len:] * (1 - fade)) + (s2[:fade_len] * fade)
        return result

    def create_stream(self) -> sd.OutputStream:
        return sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            blocksize=self.buffer_size
        )

    def write_wav(self, data: np.ndarray, filename: str):
        with wave.open(filename, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(self.sample_rate)
            f.writeframes((data * 32767).astype(np.int16).tobytes())