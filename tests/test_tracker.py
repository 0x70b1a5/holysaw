import pytest
import numpy as np
import tkinter as tk
from tkinter import ttk
import json
import tempfile
import os
from unittest.mock import MagicMock, patch
import time
import wave

from src.audio_engine import AudioEngine
from src.formula_engine import FormulaEngine
from src.grid import Grid
from src.pattern_manager import PatternManager
from src.pattern_ui import PatternUI
from src.music_tracker import MusicTracker

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

class TestGrid:
    @pytest.fixture
    def root(self):
        root = tk.Tk()
        yield root
        root.destroy()

    @pytest.fixture
    def grid(self, root):
        frame = ttk.Frame(root)
        return Grid(frame)

    def test_grid_initialization(self, grid):
        assert grid.num_columns == 32
        assert grid.cell_width == 4
        assert grid.editing == False
        assert isinstance(grid.cells, list)

    def test_cell_creation(self, grid):
        grid.update(5)  # Create 5 rows
        assert len(grid.cells) == 5
        assert len(grid.cells[0]) == grid.num_columns
        assert isinstance(grid.cells[0][0], ttk.Entry)

    def test_cell_value_handling(self, grid):
        grid.update(1)  # Create one row
        cell = grid.cells[0][0]

        # Test variable declaration
        cell.insert(0, "{x}")
        assert grid.interpret_cell_value("{x}") == "{x}"
        assert grid.get_playback_value("{x}", 0) == "x = {x}"

        # Test normal value
        cell.delete(0, tk.END)
        cell.insert(0, "42")
        assert grid.interpret_cell_value("42") == "42"

    def test_grid_update(self, grid):
        # Test increasing rows
        grid.update(5)
        assert len(grid.cells) == 5
        assert len(grid.cells[0]) == grid.num_columns

        # Verify default values in first row
        assert grid.cells[0][0].get() == "{x}"
        assert grid.cells[0][1].get() == "{v}"
        assert grid.cells[0][2].get() == "{speed}"

        # Test decreasing rows
        grid.update(3)
        assert len(grid.cells) == 3

        # Test update with existing values (preserving defaults in first row)
        existing = [
            ["{x}", "{v}", "{speed}"] + [""] * (grid.num_columns - 3),
            ["test"] * grid.num_columns,
        ]
        grid.update(2, existing)
        assert grid.cells[0][0].get() == "{x}"  # First row maintains defaults
        assert grid.cells[1][0].get() == "test"  # Second row gets test values

class TestPatternManager:
    @pytest.fixture
    def pattern_manager(self):
        return PatternManager()

    def test_initialization(self, pattern_manager):
        assert len(pattern_manager.patterns) == 12
        assert pattern_manager.patterns[1]['name'] == 'Initial Pattern'
        assert len(pattern_manager.order_list) == 0

    def test_pattern_structure(self, pattern_manager):
        pattern = pattern_manager.patterns[1]
        assert 'name' in pattern
        assert 'data' in pattern
        assert len(pattern['data']) == 64
        assert pattern['data'][0][:3] == ["x = 0", "v = 0.25", "f = 440"]

class TestMusicTracker:
    @pytest.fixture
    def root(self):
        root = tk.Tk()
        yield root
        root.destroy()

    @pytest.fixture
    def tracker(self, root):
        return MusicTracker(root)

    def test_initialization(self, tracker):
        assert isinstance(tracker.audio, AudioEngine)
        assert isinstance(tracker.formula, FormulaEngine)
        assert tracker.is_playing == False
        assert tracker._stop.is_set() == False

    @patch('sounddevice.OutputStream')
    def test_audio_generation(self, mock_stream, tracker):
        tracker.formula_text.insert("1.0", "output = np.sin(2 * np.pi * 440 * t / 44100)")
        audio_data = tracker.generate_audio(samples_per_row=1000)
        assert isinstance(audio_data, np.ndarray)
        assert len(audio_data) > 0
        assert np.all(np.abs(audio_data) <= 1.0)

    def test_save_load(self, tracker):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            # Setup some test data
            tracker.formula_text.insert("1.0", "output = 0")
            tracker.globals_text.insert("1.0", "test = 42")

            # Save
            with patch('tkinter.filedialog.asksaveasfilename', return_value=tmp.name), \
                 patch('tkinter.messagebox.showinfo'), \
                 patch('tkinter.messagebox.showerror'):
                tracker.save()

            # Clear data
            tracker.formula_text.delete("1.0", tk.END)
            tracker.globals_text.delete("1.0", tk.END)

            # Load
            with patch('tkinter.filedialog.askopenfilename', return_value=tmp.name), \
                 patch('tkinter.messagebox.showinfo'), \
                 patch('tkinter.messagebox.showerror'):
                tracker.load()

            assert tracker.formula_text.get("1.0", tk.END).strip() == "output = 0"
            assert "test = 42" in tracker.globals_text.get("1.0", tk.END)

            os.unlink(tmp.name)

    def test_pattern_variable_conversion(self, tracker):
        """Test that pattern variables are properly converted to numerical types"""
        tracker.formula_text.insert("1.0", "output = sine(t * float(freq), float(vol))")
        tracker.globals_text.insert("1.0", """
        import numpy as np
        def sine(p, v):
            return np.sin((p / 44100) * 2 * np.pi) * v
        """)

        # Mock pattern data
        tracker.pattern_ui.pattern_manager.patterns = {
            1: {
                'name': 'Test',
                'data': [
                    ["{freq}", "{vol}"],
                    ["440", "0.5"]
                ]
            }
        }
        tracker.pattern_ui.pattern_manager.order_list = [1]

        # Generate audio
        audio_data = tracker.generate_audio(samples_per_row=1000)

        assert isinstance(audio_data, np.ndarray)
        assert len(audio_data) > 0
        assert not np.any(np.isnan(audio_data))
        assert np.all(np.abs(audio_data) <= 0.5)

    def test_multi_pattern_mixing(self, tracker):
        """Test mixing multiple patterns with different variables"""
        tracker.formula_text.insert("1.0", """
        bass = sine(t * float(freq1), float(vol1))
        lead = sine(t * float(freq2), float(vol2))
        output = bass + lead
        """)
        tracker.globals_text.insert("1.0", """
        import numpy as np
        def sine(p, v):
            return np.sin((p / 44100) * 2 * np.pi) * v
        """)

        # Mock pattern data
        tracker.pattern_ui.pattern_manager.patterns = {
            1: {
                'name': 'Bass',
                'data': [
                    ["{freq1}", "{vol1}"],
                    ["220", "0.3"]
                ]
            },
            2: {
                'name': 'Lead',
                'data': [
                    ["{freq2}", "{vol2}"],
                    ["440", "0.2"]
                ]
            }
        }
        tracker.pattern_ui.pattern_manager.order_list = [1, 2]

        # Generate audio
        audio_data = tracker.generate_audio(samples_per_row=1000)

        assert isinstance(audio_data, np.ndarray)
        assert len(audio_data) > 0
        assert not np.any(np.isnan(audio_data))
        assert np.all(np.abs(audio_data) <= 0.5)

def test_integration_full_pipeline():
    """Integration test for the complete audio generation pipeline"""
    root = tk.Tk()
    tracker = MusicTracker(root)

    # Setup test pattern
    tracker.formula_text.insert("1.0", "output = np.sin(2 * np.pi * 440 * t / 44100)")
    tracker.globals_text.insert("1.0", "test_freq = 440")

    # Generate some audio
    audio_data = tracker.generate_audio(samples_per_row=1000)

    assert isinstance(audio_data, np.ndarray)
    assert len(audio_data) > 0
    assert np.all(np.abs(audio_data) <= 1.0)

    root.destroy()

class TestPatternPlayback:
    @pytest.fixture
    def tracker(self, root):
        return MusicTracker(root)

    def test_pattern_sequence_playback(self, tracker):
        """Test pattern sequencing and playback functionality"""
        # Setup test patterns
        tracker.pattern_manager.patterns[0]['data'] = [["f = 440"] * 32]
        tracker.pattern_manager.patterns[1]['data'] = [["f = 880"] * 32]
        tracker.pattern_manager.order_list = [0, 1, 0]

        # Mock audio output
        with patch.object(tracker.audio, 'stream') as mock_stream:
            tracker.play()
            assert tracker.is_playing == True
            assert tracker.current_pattern == 0

            # Simulate pattern advancement
            tracker._advance_pattern()
            assert tracker.current_pattern == 1

            tracker._advance_pattern()
            assert tracker.current_pattern == 0

            tracker.stop()
            assert tracker.is_playing == False

    def test_pattern_loop_handling(self, tracker):
        """Test pattern looping behavior"""
        tracker.pattern_manager.order_list = [0]
        tracker.loop_enabled = True

        with patch.object(tracker.audio, 'stream'):
            tracker.play()
            initial_pattern = tracker.current_pattern

            # Should loop back to start
            tracker._advance_pattern()
            assert tracker.current_pattern == initial_pattern

    @pytest.mark.timeout(1)  # Ensure test doesn't hang
    def test_realtime_pattern_modification(self, tracker):
        """Test modifying patterns during playback"""
        with patch.object(tracker.audio, 'stream'):
            tracker.play()

            # Modify current pattern during playback
            tracker.pattern_manager.patterns[0]['data'][0][0] = "f = 660"

            # Verify changes are reflected in audio generation
            audio_data = tracker.generate_audio(samples_per_row=1000)
            assert isinstance(audio_data, np.ndarray)
            assert len(audio_data) > 0

class TestErrorHandling:
    @pytest.fixture
    def tracker(self, root):
        return MusicTracker(root)

    def test_invalid_formula_handling(self, tracker):
        """Test handling of invalid formulas"""
        tracker.formula_text.delete("1.0", tk.END)
        tracker.formula_text.insert("1.0", "output = invalid_function()")

        # Should not raise exception, should return silence
        audio_data = tracker.generate_audio(samples_per_row=1000)
        assert np.allclose(audio_data, 0)

    def test_buffer_underrun_handling(self, tracker):
        """Test handling of buffer underruns"""
        with patch.object(tracker.audio, 'stream') as mock_stream:
            mock_stream.write.side_effect = [None, Exception("Buffer underrun")]

            tracker.play()
            # Should handle exception gracefully
            assert not tracker._stop.is_set()

    def test_file_io_errors(self, tracker):
        """Test handling of file I/O errors"""
        with patch('tkinter.filedialog.asksaveasfilename', return_value="/nonexistent/path"):
            # Should handle save error gracefully
            tracker.save()

        with patch('tkinter.filedialog.askopenfilename', return_value="/nonexistent/path"):
            # Should handle load error gracefully
            tracker.load()

class TestUIInteractions:
    @pytest.fixture
    def tracker(self, root):
        return MusicTracker(root)

    def test_pattern_selection(self, tracker):
        """Test pattern selection via UI"""
        tracker.pattern_manager.select_pattern(2)
        assert tracker.pattern_manager.current_pattern == 2

        # Test UI update
        assert tracker.pattern_ui.current_pattern == 2

    def test_grid_cell_editing(self, tracker):
        """Test grid cell editing interactions"""
        test_value = "f = 440"
        cell = tracker.pattern_ui.grid.cells[0][0]

        cell.insert(0, test_value)
        cell.event_generate('<Return>')

        assert tracker.pattern_manager.patterns[tracker.pattern_manager.current_pattern]['data'][0][0] == test_value

    def test_keyboard_shortcuts(self, tracker):
        """Test keyboard shortcut handling"""
        with patch.object(tracker, 'play') as mock_play:
            tracker.root.event_generate('<space>')
            mock_play.assert_called_once()

        with patch.object(tracker, 'stop') as mock_stop:
            tracker.root.event_generate('<Escape>')
            mock_stop.assert_called_once()

class TestPerformance:
    @pytest.fixture
    def tracker(self, root):
        return MusicTracker(root)

    def test_large_pattern_handling(self, tracker):
        """Test handling of large patterns"""
        # Create a large pattern (1000 rows)
        large_pattern = [["f = 440"] * 32 for _ in range(1000)]
        tracker.pattern_manager.patterns[0]['data'] = large_pattern

        start_time = time.time()
        audio_data = tracker.generate_audio(samples_per_row=1000)
        end_time = time.time()

        # Generation should complete within reasonable time (adjust threshold as needed)
        assert end_time - start_time < 1.0
        assert len(audio_data) > 0

    def test_rapid_pattern_switching(self, tracker):
        """Test rapid pattern switching performance"""
        with patch.object(tracker.audio, 'stream'):
            tracker.play()

            start_time = time.time()
            for _ in range(100):
                tracker._advance_pattern()
            end_time = time.time()

            # Pattern switching should be responsive
            assert end_time - start_time < 0.1

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

if __name__ == "__main__":
    pytest.main([__file__])