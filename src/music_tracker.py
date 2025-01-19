import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import threading
import numpy as np
from typing import Optional
import re
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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

        # Initialize globals text with content from globals.py
        self.globals_text = tk.Text(globals_frame)
        self.globals_text.pack_forget()
        
        # Load default globals from globals.py
        try:
            with open('src/globals.py', 'r') as f:
                default_globals = f.read()
            self.globals_text.insert("1.0", default_globals)
        except Exception as e:
            logger.error(f"Error loading globals.py: {e}")
            self.globals_text.insert("1.0", "")

        # Formula section
        formula_frame = ttk.LabelFrame(self.top_frame, text="Output Formula", padding=5)
        formula_frame.pack(fill=tk.X, pady=(0, 10))
        self.formula_text = tk.Text(formula_frame, height=3)
        self.formula_text.pack(fill=tk.X)
        self.formula_text.insert("1.0", "output = vibrato(saw,cents(x)*t,v,r,d)")

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
        self.grid = Grid(self.grid_frame, self.canvas)

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
        ttk.Button(controls, text="New",
                  command=self.reset_all).pack(side=tk.LEFT, padx=2)

    def cleanup_and_close(self):
        self._stop.set()
        self.is_playing = False
        if self.audio.stream:
            self.audio.stream.stop()
            self.audio.stream.close()
        self.root.destroy()

    def reset_all(self):
        """Reset everything to initial state"""
        # Reset globals
        if hasattr(self, 'globals_text'):
            self.globals_text.delete("1.0", tk.END)
        
        # Reset formula
        self.formula_text.delete("1.0", tk.END)
        
        # Reset grid
        self.rows_entry.delete(0, tk.END)
        self.rows_entry.insert(0, "64")
        self.speed_entry.delete(0, tk.END)
        self.speed_entry.insert(0, "4")
        
        # Reset pattern manager
        self.pattern_ui.pattern_manager.patterns.clear()
        self.pattern_ui.pattern_manager.order_list.clear()
        
        # Reset pattern UI
        self.pattern_ui.order_listbox.delete(0, tk.END)
        self.pattern_ui.current_pattern_number.set("1")
        self.pattern_ui.pattern_name_entry.delete(0, tk.END)
        
        # Initialize with first pattern
        self.pattern_ui.pattern_manager.order_list.append(1)
        self.pattern_ui.order_listbox.insert(tk.END, "1: Initial Pattern")
        
        # Update grid
        self.update_grid()

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
        logger.info("Starting audio generation")
        buffer = np.array([], dtype=np.float32)
        current_t = self.last_t
        logger.debug(f"Starting from t={current_t}")

        # Initialize persistent vars with defaults
        persistent_vars_dict = {
            't': 0,  # time
            'r': 5,  # default rate for modulation effects
            'd': 0.1,  # default depth for modulation effects
            'f': 440,  # default frequency
            's': 44100,  # sample rate
        }
        persistent_vars_dict.update(self.formula.globals)
        try:
            persistent_vars_dict['speed'] = float(self.speed_entry.get() or 4)
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting speed: {e}")
            persistent_vars_dict['speed'] = 4.0

        # Update globals before generation
        logger.info("Updating formula engine globals")
        globals_text = self.globals_text.get("1.0", tk.END)
        self.formula.update_globals(globals_text)
        logger.debug(f"Formula engine globals: {list(self.formula.globals.keys())}")

        # Store original function references
        function_refs = {}
        for name, value in self.formula.globals.items():
            if callable(value):
                function_refs[name] = value

        for pattern_num in self.pattern_ui.pattern_manager.order_list:
            if not self.is_playing and samples_per_row is None or self._stop.is_set():
                logger.info("Playback stopped")
                break

            logger.info(f"Processing pattern {pattern_num}")
            pattern = self.pattern_ui.pattern_manager.patterns[pattern_num]
            playback_data = self.grid.get_playback_values()
            logger.debug(f"Pattern data rows: {len(playback_data)}")

            for row_idx, row in enumerate(playback_data):
                logger.debug(f"Processing row {row_idx}")
                # Start with previous row's variables
                row_vars_dict = persistent_vars_dict.copy()
                has_updates = False

                # Process each cell in the row
                for col_idx, cell_value in enumerate(row):
                    if cell_value:
                        try:
                            logger.debug(f"Executing cell value: {cell_value}")
                            # Execute the cell value as Python code to update variables
                            exec(cell_value, self.formula.globals, row_vars_dict)
                            has_updates = True
                        except Exception as e:
                            logger.error(f"Error processing cell: {e}. Cell value: {cell_value}")

                # Calculate number of samples for this row
                try:
                    row_speed = float(row_vars_dict.get('speed', 4.0))
                    row_samples = int(44100 / row_speed) if samples_per_row is None else samples_per_row
                    logger.debug(f"Row speed: {row_speed}, samples: {row_samples}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error calculating row samples: {e}")
                    row_speed = 4.0
                    row_samples = int(44100 / row_speed) if samples_per_row is None else samples_per_row

                try:
                    # Create time array for this row
                    t = np.linspace(current_t, current_t + row_samples - 1, row_samples, dtype=np.float32)
                    logger.debug(f"Time array: {t.shape}, range: [{t[0]}, {t[-1]}]")

                    # Create interpolation factors
                    interp = np.linspace(0, 1, row_samples, dtype=np.float32)

                    # Just use the raw values without interpolation
                    interpolated_vars = row_vars_dict.copy()

                    # Update t in both dictionaries
                    interpolated_vars['t'] = t
                    self.formula.globals['t'] = t

                    # Restore function references
                    for name, func in function_refs.items():
                        interpolated_vars[name] = func
                        self.formula.globals[name] = func

                    # Execute formula with interpolated variables
                    formula_text = self.formula_text.get("1.0", tk.END)
                    local_vars = {**self.formula.globals, **interpolated_vars}
                    logger.debug(f"Executing formula with variables: {list(local_vars.keys())}")
                    logger.debug(f"Formula: {formula_text}")
                    exec(formula_text, self.formula.globals, local_vars)

                    if 'output' in local_vars:
                        output = local_vars['output']
                        logger.debug(f"Output type: {type(output)}, shape: {output.shape if isinstance(output, np.ndarray) else 'scalar'}")
                        if isinstance(output, np.ndarray):
                            buffer = np.append(buffer, output.astype(np.float32))
                        else:
                            buffer = np.append(buffer, np.full(row_samples, float(output), dtype=np.float32))
                    else:
                        logger.warning("No output variable found in formula execution")
                        buffer = np.append(buffer, np.zeros(row_samples, dtype=np.float32))

                except Exception as e:
                    logger.error(f"Error generating audio: {e}", exc_info=True)
                    buffer = np.append(buffer, np.zeros(row_samples, dtype=np.float32))

                current_t += row_samples
                persistent_vars_dict = row_vars_dict

        self.last_t = current_t
        logger.info(f"Audio generation complete. Buffer size: {len(buffer)}")
        return buffer * 0.5  # Reduce amplitude to avoid clipping

    def play_audio(self):
        logger.info("Starting audio playback")
        try:
            while not self._stop.is_set() and self.is_playing:
                audio_data = self.generate_audio()
                logger.debug(f"Generated audio data length: {len(audio_data)}")
                if self.audio.stream is None:
                    logger.info("Creating new audio stream")
                    self.audio.stream = self.audio.create_stream()
                    self.audio.stream.start()

                for i in range(0, len(audio_data), self.audio.buffer_size):
                    if self._stop.is_set() or not self.is_playing:
                        logger.info("Playback stopped")
                        break
                    chunk = audio_data[i:i + self.audio.buffer_size]
                    if len(chunk) < self.audio.buffer_size:
                        chunk = np.pad(chunk, (0, self.audio.buffer_size - len(chunk)))
                    logger.debug(f"Writing chunk {i//self.audio.buffer_size}, size: {len(chunk)}")
                    self.audio.stream.write(chunk)
        except Exception as e:
            logger.error(f"Error in audio playback: {e}", exc_info=True)
        finally:
            logger.info("Cleaning up playback")
            self.cleanup_playback()

    def highlight_current_row(self, pattern_num, row_num):
        # Clear previous highlight
        for row in self.grid.cells:
            for cell in row:
                cell.configure(background='')
        
        # Highlight current row
        if 0 <= row_num < len(self.grid.cells):
            for cell in self.grid.cells[row_num]:
                cell.configure(background='#ff6b6b')
    
        # Highlight current pattern in order list
        self.pattern_ui.order_listbox.selection_clear(0, tk.END)
        for i, pat in enumerate(self.pattern_ui.pattern_manager.order_list):
            if pat == pattern_num:
                self.pattern_ui.order_listbox.selection_set(i)
                self.pattern_ui.order_listbox.see(i)

    def toggle_play(self):
        logger.info(f"Toggle play called. Current state: {self.is_playing}")
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
                # Extract variable names from first row
                var_map = {}
                first_row = self.grid.cells[0]
                for col, cell in enumerate(first_row):
                    value = cell.get().strip()
                    var_match = re.match(r'^{(\w+)}$', value)
                    if var_match:
                        var_map[var_match.group(1)] = col

                # Prepare globals section
                globals_text = self.globals_text.get("1.0", tk.END).strip()
                imports = re.findall(r'^import\s+(.+)$', globals_text, re.MULTILINE)

                # Extract constants (assuming they're defined as NAME = VALUE)
                
                # Extract constants (handling multi-line dictionaries)
                constants = {}
                in_constant = False
                current_constant = []
                constant_name = None
                
                for line in globals_text.split('\n'):
                    if not in_constant:
                        const_match = re.match(r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$', line)
                        if const_match:
                            constant_name = const_match.group(1)
                            if '{' in line and '}' not in line:  # Start of multi-line dict
                                in_constant = True
                                current_constant = [line]
                            else:  # Single line constant
                                constants[constant_name.lower()] = const_match.group(2).strip()
                    else:
                        current_constant.append(line)
                        if '}' in line:  # End of dictionary
                            in_constant = False
                            constants[constant_name.lower()] = '\n'.join(current_constant)
                            current_constant = []
                            constant_name = None

                # Extract function definitions
                waveforms = {}
                effects = {}
                current_func = []
                for line in globals_text.split('\n'):
                    if line.startswith('def '):
                        if current_func:
                            func_text = '\n'.join(current_func)
                            func_name = current_func[0][4:current_func[0].find('(')]
                            if any(wave in func_name for wave in ['sine', 'saw', 'sq', 'tri', 'noise']):
                                waveforms[func_name] = func_text
                            elif 'effect' in func_name or func_name in ['plain', 'vib', 'tr']:
                                effects[func_name] = func_text
                            current_func = []
                        current_func.append(line)
                    elif line.strip() and current_func:
                        current_func.append(line)

                if current_func:  # Handle last function
                    func_text = '\n'.join(current_func)
                    func_name = current_func[0][4:current_func[0].find('(')]
                    if any(wave in func_name for wave in ['sine', 'saw', 'sq', 'tri', 'noise']):
                        waveforms[func_name] = func_text
                    elif 'effect' in func_name or func_name in ['plain', 'vib', 'tr']:
                        effects[func_name] = func_text

                # Collect pattern data
                patterns = {}
                for pattern_num, pattern in self.pattern_ui.pattern_manager.patterns.items():
                    pattern_data = pattern['data'] if isinstance(pattern, dict) else pattern
                    rows = {}
                    for row_idx, row in enumerate(pattern_data):
                        row_data = {}
                        has_data = False
                        for col_idx, value in enumerate(row):
                            if value.strip() and not re.match(r'^{.*}$', value):
                                has_data = True
                                for var_name, col in var_map.items():
                                    if col == col_idx:
                                        row_data[var_name] = value
                                        break
                        if has_data:
                            rows[str(row_idx)] = row_data

                    if rows:
                        patterns[str(pattern_num)] = {
                            "name": pattern.get('name', f'Pattern {pattern_num}') if isinstance(pattern, dict) else f'Pattern {pattern_num}',
                            "rows": rows
                        }

                state = {
                    "version": "1.0",
                    "settings": {
                        "rows": int(self.rows_entry.get()),
                        "speed": float(self.speed_entry.get()),
                        "base_freq": 440.0
                    },
                    "vars": list(var_map.keys()),
                    "globals": {
                        "imports": imports,
                        "constants": constants,
                        "waveforms": waveforms,
                        "effects": effects
                    },
                    "formula": self.formula_text.get("1.0", tk.END).strip(),
                    "patterns": patterns,
                    "order": self.pattern_ui.pattern_manager.order_list,
                    "current_pattern": self.pattern_ui.current_pattern_number.get()
                }

                with open(path, 'w') as f:
                    json.dump(state, f, indent=2)
                messagebox.showinfo("Success", "Project saved successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load(self):
        try:
            path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
            if path:
                # Clear existing state first
                self.clear_state()
                
                with open(path) as f:
                    state = json.load(f)

                # Check version
                if state.get('version', "0") != "1.0":
                    raise ValueError("Unsupported file version")

                # Load settings
                self.rows_entry.delete(0, tk.END)
                self.rows_entry.insert(0, state['settings']['rows'])
                self.speed_entry.delete(0, tk.END)
                self.speed_entry.insert(0, state['settings']['speed'])

                # Reconstruct globals
                globals_text = []
                for imp in state['globals']['imports']:
                    globals_text.append(f"import {imp}")
                globals_text.append("")

                for name, value in state['globals']['constants'].items():
                    globals_text.append(f"{name.upper()} = {value}")
                globals_text.append("")

                for name, func in state['globals']['waveforms'].items():
                    globals_text.append(func)
                    globals_text.append("")

                for name, func in state['globals']['effects'].items():
                    globals_text.append(func)
                    globals_text.append("")

                self.globals_text.delete("1.0", tk.END)
                self.globals_text.insert("1.0", '\n'.join(globals_text))

                # Load formula
                self.formula_text.delete("1.0", tk.END)
                self.formula_text.insert("1.0", state['formula'])

                # Create variable mapping
                var_list = state['vars']
                var_map = {var: idx for idx, var in enumerate(var_list)}

                # Create empty grid with variable declarations
                max_col = len(var_list)
                rows = int(state['settings']['rows'])
                grid_data = [['' for _ in range(max_col)] for _ in range(rows)]

                # Fill in variable declarations in first row
                for var, col in var_map.items():
                    grid_data[0][col] = f"{{{var}}}"

                # Convert patterns to grid format
                patterns = {}
                for pattern_num, pattern in state['patterns'].items():
                    pattern_data = [row[:] for row in grid_data]  # Deep copy
                    for row_idx_str, row_data in pattern['rows'].items():
                        row_idx = int(row_idx_str)
                        for var_name, value in row_data.items():
                            if var_name in var_map:
                                col = var_map[var_name]
                                # For variables that need assignment
                                if var_name in ['pitch', 'freq', 'freq1', 'freq2', 'freq3', 'cutoff']:
                                    pattern_data[row_idx][col] = f"{var_name} = {value}"
                                else:
                                    pattern_data[row_idx][col] = value

                    patterns[int(pattern_num)] = {
                        'name': pattern['name'],
                        'data': pattern_data
                    }

                # Update pattern manager
                self.pattern_ui.pattern_manager.patterns = patterns
                self.pattern_ui.pattern_manager.order_list = [int(x) for x in state['order']]

                # Update order listbox
                self.pattern_ui.order_listbox.delete(0, tk.END)
                for pattern_num in state['order']:
                    pattern = patterns[int(pattern_num)]
                    self.pattern_ui.order_listbox.insert(tk.END, f"{pattern_num}: {pattern['name']}")

                # Load first pattern
                if state['order']:
                    first_pattern = int(state['order'][0])
                    self.pattern_ui.current_pattern_number.set(str(first_pattern))
                    if first_pattern in patterns:
                        self.grid.update(rows, patterns[first_pattern]['data'])

                # Update globals
                self.formula.update_globals(self.globals_text.get("1.0", tk.END))

                messagebox.showinfo("Load Successful", "Project loaded successfully")
        except Exception as e:
            logger.error(f"Error loading file: {e}", exc_info=True)
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

    def clear_state(self):
        # Clear patterns
        self.pattern_ui.pattern_manager.patterns.clear()
        self.pattern_ui.pattern_manager.order_list.clear()
        
        # Clear UI elements
        self.pattern_ui.order_listbox.delete(0, tk.END)
        self.pattern_ui.pattern_name_entry.delete(0, tk.END)
        
        # Clear grid
        for row in self.grid.cells:
            for cell in row:
                cell.delete(0, tk.END)
                
        # Clear text fields
        self.formula_text.delete("1.0", tk.END)
        self.globals_text.delete("1.0", tk.END)
        
        # Reset entries
        self.rows_entry.delete(0, tk.END)
        self.speed_entry.delete(0, tk.END)

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