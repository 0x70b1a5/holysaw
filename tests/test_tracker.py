import pytest
import numpy as np
import tkinter as tk
from tkinter import ttk
import json
import tempfile
import os
from unittest.mock import MagicMock, patch

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
        assert stream.dtype == np.float32

class TestFormulaEngine:
    @pytest.fixture
    def formula_engine(self):
        return FormulaEngine()

    def test_update_globals(self, formula_engine):
        test_code = """
        x = 42
        def test_func(t):
            return t * 2
        """
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

        # Test decreasing rows
        grid.update(3)
        assert len(grid.cells) == 3

        # Test update with existing values
        existing = [["test"] * grid.num_columns]
        grid.update(1, existing)
        assert grid.cells[0][0].get() == "test"

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
            with patch('tkinter.filedialog.asksaveasfilename', return_value=tmp.name):
                tracker.save()

            # Clear data
            tracker.formula_text.delete("1.0", tk.END)
            tracker.globals_text.delete("1.0", tk.END)

            # Load
            with patch('tkinter.filedialog.askopenfilename', return_value=tmp.name):
                tracker.load()

            assert tracker.formula_text.get("1.0", tk.END).strip() == "output = 0"
            assert "test = 42" in tracker.globals_text.get("1.0", tk.END)

            os.unlink(tmp.name)

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

if __name__ == "__main__":
    pytest.main([__file__])