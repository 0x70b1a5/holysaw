import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import threading
import numpy as np
from typing import Optional
import re

from .audio_engine import AudioEngine
from .formula_engine import FormulaEngine
from .grid import Grid
from .pattern_ui import PatternUI

class MusicTracker:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Music Tracker")
        self.audio = AudioEngine()
        self.formula = FormulaEngine()
        self.is_playing = False
        self._stop = threading.Event()
        self.last_t = 0

        self.setup_ui()
        self._setup_bindings()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._setup_top_frame(main_frame)
        self._setup_grid_frame(main_frame)
        self._setup_controls(main_frame)

        # Initialize PatternUI
        self.pattern_ui = PatternUI(self.top_frame, self)
        self.pattern_ui.current_pattern_number.set("1")

    def _setup_bindings(self):
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup_and_close)
        self.root.bind('<F5>', lambda e: self.toggle_play())
        self.grid_frame.bind('<F5>', lambda e: self.toggle_play())

    def _setup_top_frame(self, main_frame):
        self.top_frame = ttk.Frame(main_frame)
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)

        # Globals section
        globals_frame = ttk.Frame(self.top_frame)
        globals_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(globals_frame, text="Edit Global Variables",
                  command=self.show_globals_dialog).pack()

        self.globals_text = tk.Text(globals_frame)
        self.globals_text.pack_forget()

        # Formula section
        formula_frame = ttk.LabelFrame(self.top_frame, text="Output Formula", padding=5)
        formula_frame.pack(fill=tk.X, pady=(0, 10))
        self.formula_text = tk.Text(formula_frame, height=3)
        self.formula_text.pack(fill=tk.X)

    def _setup_grid_frame(self, main_frame):
        scroll_frame = ttk.Frame(main_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(scroll_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        h_scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create canvas
        self.canvas = tk.Canvas(scroll_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbars
        v_scrollbar.configure(command=self.canvas.yview)
        h_scrollbar.configure(command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set,
                            xscrollcommand=h_scrollbar.set)

        # Create grid frame
        self.grid_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor='nw')

        # Create Grid
        self.grid = Grid(self.grid_frame)

    def _setup_controls(self, main_frame):
        controls = ttk.Frame(main_frame)
        controls.pack(fill=tk.X, padx=10, pady=10, side=tk.BOTTOM)

        # Add rows control
        rows_frame = ttk.Frame(controls)
        rows_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(rows_frame, text="Rows:").pack(side=tk.LEFT)
        self.rows_entry = ttk.Entry(rows_frame, width=5)
        self.rows_entry.pack(side=tk.LEFT, padx=2)
        self.rows_entry.insert(0, "64")

        # Add speed control
        speed_frame = ttk.Frame(controls)
        speed_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(speed_frame, text="Speed (rows/sec):").pack(side=tk.LEFT)
        self.speed_entry = ttk.Entry(speed_frame, width=5)
        self.speed_entry.pack(side=tk.LEFT, padx=2)
        self.speed_entry.insert(0, "4")

        self.play_button = ttk.Button(controls, text="Play", command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT, padx=2)

        ttk.Button(controls, text="Export WAV",
                  command=self.export_wav).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="Save",
                  command=self.save).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="Load",
                  command=self.load).pack(side=tk.LEFT, padx=2)

    def cleanup_and_close(self):
        self._stop.set()
        self.is_playing = False
        if self.audio.stream:
            self.audio.stream.stop()
            self.audio.stream.close()
        self.root.destroy()

    def show_globals_dialog(self):
        """Show global variables in a popup dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Global Variables")
        dialog.geometry("600x400")

        text = tk.Text(dialog, height=20)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        if hasattr(self, 'globals_text'):
            text.insert("1.0", self.globals_text.get("1.0", tk.END))

        def save_and_close():
            if hasattr(self, 'globals_text'):
                self.globals_text.delete("1.0", tk.END)
                self.globals_text.insert("1.0", text.get("1.0", tk.END))
            else:
                self.globals_text = text
            self.formula.update_globals(text.get("1.0", tk.END))
            dialog.destroy()

        ttk.Button(dialog, text="Save & Close", command=save_and_close).pack(pady=10)

    def generate_audio(self, samples_per_row=None):
        buffer = np.array([], dtype=np.float32)
        current_t = self.last_t

        # Collect all possible variables
        all_variables = set()
        formula_text = self.formula_text.get("1.0", tk.END)
        globals_text = self.globals_text.get("1.0", tk.END)
        all_variables.update(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', formula_text))
        all_variables.update(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', globals_text))

        for row in self.grid.cells:
            for cell in row:
                value = cell.get().strip()
                var_match = re.match(r'^{(\w+)}$', value)
                if var_match:
                    all_variables.add(var_match.group(1))

        # Initialize persistent vars
        persistent_vars_dict = {var: 0 for var in all_variables}
        persistent_vars_dict.update(self.formula.globals)
        try:
            persistent_vars_dict['speed'] = float(self.speed_entry.get() or 4)
        except (ValueError, TypeError):
            persistent_vars_dict['speed'] = 4.0

        # Update globals before generation
        self.formula.update_globals(globals_text)

        for pattern_num in self.pattern_ui.pattern_manager.order_list:
            if not self.is_playing and samples_per_row is None or self._stop.is_set():
                break

            pattern = self.pattern_ui.pattern_manager.patterns[pattern_num]
            playback_data = self.grid.get_playback_values()

            for row_idx, row in enumerate(playback_data):
                row_vars_dict = persistent_vars_dict.copy()
                has_updates = False

                # Store previous row's values for interpolation
                prev_vars_dict = row_vars_dict.copy()

                for col_idx, cell_value in enumerate(row):
                    if cell_value.strip():
                        has_updates = True
                        try:
                            exec(cell_value, {}, row_vars_dict)
                        except Exception as e:
                            print(f"Error in row {row_idx}, col {col_idx}: {e}")

                if 'speed' in row_vars_dict:
                    try:
                        speed_value = float(row_vars_dict['speed'])
                        persistent_vars_dict['speed'] = speed_value
                    except (ValueError, TypeError):
                        pass

                try:
                    row_speed = max(0.1, float(persistent_vars_dict['speed']))
                except (ValueError, TypeError):
                    row_speed = 4.0

                if samples_per_row is None:
                    row_samples = int(44100 / row_speed)
                else:
                    row_samples = samples_per_row

                # Generate time array for this row
                t = np.linspace(current_t, current_t + row_samples - 1, row_samples, dtype=np.float32)

                if has_updates:
                    try:
                        # Create interpolation factors
                        interp = np.linspace(0, 1, row_samples)[:, np.newaxis]

                        # Interpolate numerical variables
                        interpolated_vars = {}
                        for var in row_vars_dict:
                            if var in prev_vars_dict and isinstance(row_vars_dict[var], (int, float)):
                                start_val = float(prev_vars_dict[var])
                                end_val = float(row_vars_dict[var])
                                interpolated_vars[var] = start_val + (end_val - start_val) * interp
                            else:
                                interpolated_vars[var] = row_vars_dict[var]

                        # Update t in both dictionaries
                        interpolated_vars['t'] = t
                        self.formula.globals['t'] = t

                        # Execute formula with interpolated variables
                        exec(formula_text, self.formula.globals, interpolated_vars)
                        if 'output' in interpolated_vars:
                            output = interpolated_vars['output']
                            if isinstance(output, np.ndarray):
                                buffer = np.append(buffer, output.astype(np.float32))
                            else:
                                buffer = np.append(buffer, np.full(row_samples, output, dtype=np.float32))
                    except Exception as e:
                        print(f"Error generating audio: {e}")
                        buffer = np.append(buffer, np.zeros(row_samples, dtype=np.float32))
                else:
                    buffer = np.append(buffer, np.zeros(row_samples, dtype=np.float32))

                current_t += row_samples

        self.last_t = current_t
        return buffer * 0.5

    def play_audio(self):
        try:
            while not self._stop.is_set() and self.is_playing:
                audio_data = self.generate_audio()
                if self.audio.stream is None:
                    self.audio.stream = self.audio.create_stream()
                    self.audio.stream.start()

                for i in range(0, len(audio_data), self.audio.buffer_size):
                    if self._stop.is_set() or not self.is_playing:
                        break
                    chunk = audio_data[i:i + self.audio.buffer_size]
                    if len(chunk) < self.audio.buffer_size:
                        chunk = np.pad(chunk, (0, self.audio.buffer_size - len(chunk)))
                    self.audio.stream.write(chunk)
        finally:
            self.cleanup_playback()

    def toggle_play(self):
        self.formula.update_globals(self.globals_text.get("1.0", tk.END))
        if self.is_playing:
            self._stop.set()
            self.is_playing = False
            self.play_button.configure(text="Play")
            self.formula.reset_phases()
        else:
            self._stop.clear()
            self.is_playing = True
            self.play_button.configure(text="Stop")
            self.formula.reset_phases()
            threading.Thread(target=self.play_audio, daemon=True).start()

    def cleanup_playback(self):
        self.is_playing = False
        self._stop.clear()
        self.play_button.configure(text="Play")
        self.last_t = 0
        if self.audio.stream:
            self.audio.stream.stop()
            self.audio.stream.close()
            self.audio.stream = None

    def save(self):
        try:
            path = filedialog.asksaveasfilename(defaultextension=".json")
            if path:
                state = {
                    'globals': self.globals_text.get("1.0", tk.END),
                    'formula': self.formula_text.get("1.0", tk.END),
                    'rows': self.rows_entry.get(),
                    'speed': self.speed_entry.get(),
                    'grid': self.grid.get_values(),
                    'patterns': self.pattern_ui.pattern_manager.patterns,
                    'order': self.pattern_ui.pattern_manager.order_list,
                    'current_pattern': self.pattern_ui.current_pattern_number.get()
                }
                with open(path, 'w') as f:
                    json.dump(state, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load(self):
        try:
            path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
            if path:
                with open(path) as f:
                    state = json.load(f)

                self.globals_text.delete("1.0", tk.END)
                self.globals_text.insert("1.0", state['globals'])
                self.formula_text.delete("1.0", tk.END)
                self.formula_text.insert("1.0", state['formula'])

                self.rows_entry.delete(0, tk.END)
                self.rows_entry.insert(0, state['rows'])
                self.speed_entry.delete(0, tk.END)
                self.speed_entry.insert(0, state['speed'])

                patterns = state.get('patterns', {})
                patterns = {int(k): v for k, v in patterns.items()}

                if patterns and isinstance(next(iter(patterns.values())), list):
                    self.pattern_ui.pattern_manager.patterns = {
                        num: {'name': f'Pattern {num}', 'data': data}
                        for num, data in patterns.items()
                    }
                else:
                    self.pattern_ui.pattern_manager.patterns = patterns

                self.pattern_ui.order_listbox.delete(0, tk.END)
                restored_order = state.get('order', [])
                self.pattern_ui.pattern_manager.order_list = restored_order

                for pattern_num in restored_order:
                    pattern = self.pattern_ui.pattern_manager.patterns[pattern_num]
                    if isinstance(pattern, dict):
                        pattern_name = pattern.get('name', f'Pattern {pattern_num}')
                    else:
                        pattern_name = f'Pattern {pattern_num}'
                    self.pattern_ui.order_listbox.insert(tk.END, f"{pattern_num}: {pattern_name}")

                current_pattern = state.get('current_pattern', '1')
                self.pattern_ui.current_pattern_number.set(current_pattern)

                if current_pattern:
                    pattern_num = int(current_pattern)
                    if pattern_num in self.pattern_ui.pattern_manager.patterns:
                        pattern = self.pattern_ui.pattern_manager.patterns[pattern_num]
                        if isinstance(pattern, dict):
                            self.grid.update(int(state['rows']), pattern['data'])
                        else:
                            self.grid.update(int(state['rows']), pattern)

                self.formula.update_globals(state['globals'])

                messagebox.showinfo("Load Successful", "Project loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_wav(self):
        try:
            path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav")]
            )
            if not path:
                return

            self.formula.update_globals(self.globals_text.get("1.0", tk.END))

            order_list = self.pattern_ui.pattern_manager.order_list
            if not order_list:
                messagebox.showerror("Error", "No patterns in play order to export")
                return

            audio_data = self.generate_audio(samples_per_row=5000)
            self.audio.write_wav(audio_data, path)

            messagebox.showinfo("Success", f"Audio exported to {path}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def update_grid(self):
        """Update the grid with the current pattern data"""
        try:
            rows = max(1, int(self.rows_entry.get()))
            existing = self.grid.get_values() if hasattr(self, 'grid') else None
            self.grid.update(rows, existing)

            # Auto-save pattern when row count changes
            try:
                pattern_num = int(self.pattern_ui.current_pattern_number.get())
                if pattern_num in self.pattern_ui.pattern_manager.patterns:
                    pattern = self.pattern_ui.pattern_manager.patterns[pattern_num]
                    if isinstance(pattern, dict):
                        pattern['data'] = self.grid.get_values()
            except ValueError:
                pass

            # Update scroll region
            self.grid_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            messagebox.showerror("Error", str(e))