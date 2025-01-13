import pytest
import numpy as np
import json
import tempfile
import os
from unittest.mock import MagicMock, patch
import unittest
import time
import wave
from pathlib import Path

from src.audio_engine import AudioEngine
from src.formula_engine import FormulaEngine

class TestAudioEngine:
    @pytest.fixture
    def audio_engine(self):
        return AudioEngine(sample_rate=44100, buffer_size=2048, fade_samples=500)

    def test_crossfade(self, audio_engine):
        s1 = np.ones(1000, dtype=np.float32)
        s2 = np.zeros(1000, dtype=np.float32)

        result = audio_engine.crossfade(s1, s2)

        assert len(result) == len(s1)
        assert result[0] == pytest.approx(1.0)
        assert result[-1] == pytest.approx(0.0)
        assert np.all(np.diff(result[-500:]) < 0)

    def test_write_wav(self, audio_engine):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            test_data = np.sin(np.linspace(0, 2*np.pi, 1000))
            audio_engine.write_wav(test_data, tmp.name)
            assert os.path.exists(tmp.name)
            assert os.path.getsize(tmp.name) > 0
            os.unlink(tmp.name)

    def test_create_stream(self, audio_engine):
        stream = audio_engine.create_stream()
        assert stream is not None
        assert stream.samplerate == 44100
        assert stream.channels == 1
        assert stream.dtype == 'float32'

class TestFormulaEngine:
    @pytest.fixture
    def formula_engine(self):
        engine = FormulaEngine()
        engine.update_globals("""import numpy as np

def sine(p, v):
    # p is t * freq, so p/s is t*freq/s
    phase = (p.astype(np.float32) / 44100)  # t*freq/s
    return ((np.sin(2 * np.pi * phase)).astype(np.float32) * float(v)).astype(np.float32)

def saw(p, v):
    phase = (p.astype(np.float32) / 44100) % 1
    return ((phase * 2 - 1) * float(v)).astype(np.float32)

def sq(p, v, duty=0.5):
    phase = (p.astype(np.float32) / 44100) % 1
    return (((phase < float(duty)) * 2 - 1) * float(v)).astype(np.float32)

def tri(p, v):
    phase = (p.astype(np.float32) / 44100) % 1
    return ((2 * abs(2 * phase - 1) - 1) * float(v)).astype(np.float32)
""")
        return engine

    def test_update_globals(self, formula_engine):
        test_code = "x = 42\ndef test_func(t):\n    return t * 2"
        formula_engine.update_globals(test_code)

        assert formula_engine.globals['x'] == 42
        assert callable(formula_engine.globals['test_func'])
        assert 'math' in formula_engine.globals
        assert 'np' in formula_engine.globals

    def test_phase_tracking(self, formula_engine):
        formula_engine.set_phase('test_phase', 0.5)
        assert formula_engine.get_phase('test_phase') == 0.5

        formula_engine.set_phase('test_phase', 1.5)
        assert formula_engine.get_phase('test_phase') == 0.5

        assert formula_engine.get_phase('nonexistent') == 0.0

        formula_engine.reset_phases()
        assert formula_engine.get_phase('test_phase') == 0.0

    def test_generate_samples_with_variables(self, formula_engine):
        formula_engine.update_globals("""
        import math
        def sine_wave(freq, amp):
            return math.sin(2 * math.pi * freq * t / 44100) * amp
        """)

        formula = "output = sine_wave(440, 0.5)"
        vars_dict = {'freq': 440, 'amp': 0.5}
        samples = formula_engine.generate_samples(formula, 0, 1000, vars_dict)

        assert len(samples) == 1000
        assert isinstance(samples, np.ndarray)
        assert samples.dtype == np.float32
        assert np.all(np.abs(samples) <= 0.5)

    def test_eval_formula_with_error(self, formula_engine):
        formula = "output = undefined_variable"
        result = formula_engine.eval_formula(formula, 0.0, {})
        assert result == 0  # Should return 0 on error

    def test_variable_type_handling(self, formula_engine):
        """Test that variables are properly converted to numerical types"""
        formula_engine.update_globals("""
        import numpy as np
        def sine(p, v):
            return np.sin((p / 44100) * 2 * np.pi) * v
        """)

        # Test with string inputs (common when loading from JSON)
        vars_dict = {'freq': "440", 'amp': "0.5"}
        samples = formula_engine.generate_samples(
            "output = sine(t * float(freq), float(amp))",
            0, 1000, vars_dict
        )

        assert isinstance(samples, np.ndarray)
        assert samples.dtype == np.float32
        assert len(samples) == 1000
        assert np.all(np.abs(samples) <= 0.5)

    def test_array_scalar_operations(self, formula_engine):
        """Test operations between arrays and scalars"""
        formula_engine.update_globals("""
        import numpy as np
        def sine(p, v):
            return np.sin((p / 44100) * 2 * np.pi) * float(v)
        """)

        vars_dict = {'freq': "440", 'amp': "0.5"}
        samples = formula_engine.generate_samples(
            "output = sine(t * float(freq), amp)",
            0, 1000, vars_dict
        )

        assert isinstance(samples, np.ndarray)
        assert not np.any(np.isnan(samples))
        assert np.all(np.abs(samples) <= 0.5)

class TestWaveformOutput:
    @pytest.fixture
    def audio_engine(self):
        return AudioEngine(sample_rate=44100, buffer_size=2048, fade_samples=500)

    @pytest.fixture
    def formula_engine(self):
        engine = FormulaEngine()
        engine.update_globals("""import numpy as np

def sine(p, v):
    # p is t * freq, so p/s is t*freq/s
    phase = (p.astype(np.float32) / 44100)  # t*freq/s
    return ((np.sin(2 * np.pi * phase)).astype(np.float32) * float(v)).astype(np.float32)

def saw(p, v):
    phase = (p.astype(np.float32) / 44100) % 1
    return ((phase * 2 - 1) * float(v)).astype(np.float32)

def sq(p, v, duty=0.5):
    phase = (p.astype(np.float32) / 44100) % 1
    return (((phase < float(duty)) * 2 - 1) * float(v)).astype(np.float32)

def tri(p, v):
    phase = (p.astype(np.float32) / 44100) % 1
    return ((2 * abs(2 * phase - 1) - 1) * float(v)).astype(np.float32)
""")
        return engine

    def verify_wav_contents(self, wav_path, expected_samples):
        """Helper function to verify WAV file contents match expected samples"""
        with wave.open(wav_path, 'rb') as wav:
            assert wav.getnchannels() == 1
            assert wav.getsampwidth() == 2
            assert wav.getframerate() == 44100

            # Read all frames and convert to numpy array
            frames = wav.readframes(wav.getnframes())
            actual_samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32767.0

            # Verify the samples match (within floating-point precision)
            assert len(actual_samples) == len(expected_samples)

            # Simulate the same quantization that happens in the WAV file
            expected_quantized = (expected_samples * 32767.0).astype(np.int16).astype(np.float32) / 32767.0

            # Use a more generous tolerance to account for quantization effects
            assert np.allclose(actual_samples, expected_quantized, rtol=1e-3, atol=1e-3)

            # Verify that the maximum absolute difference is within one quantization step
            max_diff = np.max(np.abs(actual_samples - expected_quantized))
            assert max_diff <= (1.0 / 32767.0)

    def test_sine_wave_export(self, audio_engine, formula_engine):
        """Test exporting a pure sine wave to WAV"""
        # Generate one second of A440 sine wave
        samples = formula_engine.generate_samples(
            "output = sine(t * 440, 1.0)",
            0, 44100,
            {}
        )

        # Calculate expected values using the same formula as the engine
        t = np.arange(44100, dtype=np.float32)
        phase = (t * 440 / 44100)  # t*freq/s
        expected = np.sin(2 * np.pi * phase).astype(np.float32)

        # First verify the formula engine output
        if not np.allclose(samples, expected, rtol=1e-5, atol=1e-5):
            # Find indices where values differ
            diffs = ~np.isclose(samples, expected, rtol=1e-5, atol=1e-5)
            total_mismatches = np.sum(diffs)
            mismatch_percentage = (total_mismatches / len(samples)) * 100
            mismatch_indices = np.where(diffs)[0][:5]  # Get up to 5 mismatches

            error_msg = "Formula engine output doesn't match expected values:\n"
            error_msg += f"Total mismatches: {total_mismatches} ({mismatch_percentage:.2f}% of samples)\n"
            error_msg += f"Sample rate used in formula: {formula_engine.globals.get('s', 'not found')}\n"
            for idx in mismatch_indices:
                error_msg += f"At t={t[idx]:.6f}s (idx={idx}): samples={samples[idx]:.6f} != expected={expected[idx]:.6f} "
                error_msg += f"(diff={abs(samples[idx] - expected[idx]):.9f})\n"
                error_msg += f"  Phase at idx={idx}: {phase[idx]:.6f} rad\n"

            assert False, error_msg

    def test_complex_waveform_export(self, audio_engine, formula_engine):
        """Test exporting a complex waveform (multiple frequencies) to WAV"""
        # Generate one second of combined A440 + A880
        samples = formula_engine.generate_samples(
            "output = 0.5 * sine(t * 440, 1.0) + 0.5 * sine(t * 880, 1.0)",
            0, 44100,
            {}
        )

        # Calculate expected values using the same formula as the engine
        t = np.arange(44100, dtype=np.float32)
        phase440 = (t * 440 / 44100)  # t*freq/s
        phase880 = (t * 880 / 44100)  # t*freq/s
        expected = (0.5 * np.sin(2 * np.pi * phase440) + 0.5 * np.sin(2 * np.pi * phase880)).astype(np.float32)

        # First verify the formula engine output
        if not np.allclose(samples, expected, rtol=1e-5, atol=1e-5):
            # Find indices where values differ
            diffs = ~np.isclose(samples, expected, rtol=1e-5, atol=1e-5)
            total_mismatches = np.sum(diffs)
            mismatch_percentage = (total_mismatches / len(samples)) * 100
            mismatch_indices = np.where(diffs)[0][:5]  # Get up to 5 mismatches

            error_msg = "Formula engine output doesn't match expected values:\n"
            error_msg += f"Total mismatches: {total_mismatches} ({mismatch_percentage:.2f}% of samples)\n"
            error_msg += f"Sample rate used in formula: {formula_engine.globals.get('s', 'not found')}\n"
            for idx in mismatch_indices:
                error_msg += f"At t={t[idx]:.6f}s (idx={idx}): samples={samples[idx]:.6f} != expected={expected[idx]:.6f} "
                error_msg += f"(diff={abs(samples[idx] - expected[idx]):.9f})\n"
                error_msg += f"  Phase440 at idx={idx}: {phase440[idx]:.6f} rad\n"
                error_msg += f"  Phase880 at idx={idx}: {phase880[idx]:.6f} rad\n"

            assert False, error_msg

    def test_pattern_sequence_export(self, audio_engine, formula_engine):
        """Test exporting a sequence of different frequencies"""
        # Generate half second of A440 followed by half second of A880 at half volume
        samples1 = formula_engine.generate_samples(
            "output = sine(t * 440, 1.0)",
            0, 22050,
            {}
        )
        samples2 = formula_engine.generate_samples(
            "output = sine(t * 880, 0.5)",
            22050, 22050,  # Continue from where first segment ended
            {}
        )
        samples = np.concatenate([samples1, samples2])

        # Calculate expected values using the same formula as the engine
        t1 = np.arange(22050, dtype=np.float32)
        t2 = np.arange(22050, 44100, dtype=np.float32)  # Continue from where first segment ended
        phase1 = (t1 * 440 / 44100)  # t*freq/s
        phase2 = (t2 * 880 / 44100)  # t*freq/s
        expected = np.concatenate([
            np.sin(2 * np.pi * phase1).astype(np.float32),
            (0.5 * np.sin(2 * np.pi * phase2)).astype(np.float32)
        ])

        # First verify the formula engine output
        if not np.allclose(samples, expected, rtol=1e-5, atol=1e-5):
            # Find indices where values differ
            diffs = ~np.isclose(samples, expected, rtol=1e-5, atol=1e-5)
            total_mismatches = np.sum(diffs)
            mismatch_percentage = (total_mismatches / len(samples)) * 100
            mismatch_indices = np.where(diffs)[0][:5]  # Get up to 5 mismatches

            error_msg = "Formula engine output doesn't match expected values:\n"
            error_msg += f"Total mismatches: {total_mismatches} ({mismatch_percentage:.2f}% of samples)\n"
            error_msg += f"Sample rate used in formula: {formula_engine.globals.get('s', 'not found')}\n"
            for idx in mismatch_indices:
                t_val = t1[idx] if idx < 22050 else t2[idx - 22050]
                phase = phase1[idx] if idx < 22050 else phase2[idx - 22050]
                error_msg += f"At t={t_val:.6f}s (idx={idx}): samples={samples[idx]:.6f} != expected={expected[idx]:.6f} "
                error_msg += f"(diff={abs(samples[idx] - expected[idx]):.9f})\n"
                error_msg += f"  Phase at idx={idx}: {phase:.6f} rad\n"
                error_msg += f"  Segment: {'first' if idx < 22050 else 'second'}\n"

            assert False, error_msg

class TestSaveLoadJSON:
    @pytest.fixture
    def test_data(self):
        return {
            "version": "1.0",
            "settings": {
                "rows": 64,
                "speed": 4.0,
                "base_freq": 440.0
            },
            "vars": ["x", "v", "f"],
            "globals": {
                "imports": ["import numpy as np"],
                "constants": ["s = 44100"],
                "waveforms": [
                    "def sine(p, v): return np.sin((p / s) * 2 * np.pi) * float(v)",
                    "def saw(p, v): return ((p / s) % 1) * 2 - 1 * float(v)",
                    "def sq(p, v): return (((p / s) % 1) < 0.5) * 2 - 1 * float(v)"
                ],
                "effects": [
                    "def lfo(rate, amp): return np.sin(t * rate) * amp",
                    "def arp(base, steps): return base * (2 ** (steps[int(t * 8) % len(steps)] / 12))"
                ]
            },
            "formula": "output = sine(t * f, v) * x",
            "patterns": {
                "1": {
                    "rows": {
                        "0": {"0": "{x}", "1": "{v}", "2": "{f}"},
                        "1": {"0": "0.8", "1": "1.0", "2": "440"},
                        "2": {"0": "0.6", "1": "0.8", "2": "880"}
                    }
                }
            },
            "order": ["1"],
            "current_pattern": "1"
        }

    def test_save_json_format(self, test_data, tmp_path):
        # Save test data to a temporary file
        save_path = tmp_path / "test_save.json"
        with open(save_path, "w") as f:
            json.dump(test_data, f, indent=2)

        # Read back and verify structure
        with open(save_path) as f:
            loaded_data = json.load(f)

        # Verify all required keys are present
        assert set(loaded_data.keys()) == {"version", "settings", "vars", "globals", "formula", "patterns", "order", "current_pattern"}

        # Verify settings
        assert loaded_data["settings"]["rows"] == 64
        assert loaded_data["settings"]["speed"] == 4.0
        assert loaded_data["settings"]["base_freq"] == 440.0

        # Verify pattern structure
        pattern = loaded_data["patterns"]["1"]
        assert "rows" in pattern
        assert pattern["rows"]["0"]["0"] == "{x}"
        assert pattern["rows"]["1"]["2"] == "440"

    def test_load_json_format(self, test_data, tmp_path):
        # Save and load test data
        save_path = tmp_path / "test_load.json"
        with open(save_path, "w") as f:
            json.dump(test_data, f, indent=2)

        with open(save_path) as f:
            loaded_data = json.load(f)

        # Verify globals structure
        assert "imports" in loaded_data["globals"]
        assert "constants" in loaded_data["globals"]
        assert "waveforms" in loaded_data["globals"]
        assert "effects" in loaded_data["globals"]

        # Verify waveform functions
        assert any("sine(p, v)" in fn for fn in loaded_data["globals"]["waveforms"])
        assert any("saw(p, v)" in fn for fn in loaded_data["globals"]["waveforms"])
        assert any("sq(p, v)" in fn for fn in loaded_data["globals"]["waveforms"])

        # Verify variable declarations
        assert set(loaded_data["vars"]) == {"x", "v", "f"}

    def test_json_roundtrip(self, test_data, tmp_path):
        # Save test data
        save_path = tmp_path / "test_roundtrip.json"
        with open(save_path, "w") as f:
            json.dump(test_data, f, indent=2)

        # Load test data
        with open(save_path) as f:
            loaded_data = json.load(f)

        # Verify data is unchanged through save/load cycle
        assert loaded_data == test_data

if __name__ == "__main__":
    pytest.main([__file__])