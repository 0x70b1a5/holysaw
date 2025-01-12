import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import numpy as np
import re
import sounddevice as sd
import wave, math, json, threading
from typing import Dict, List, Optional

class AudioEngine:
    def __init__(self, sample_rate=44100, buffer_size=2048, fade_samples=500):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.fade_samples = fade_samples
        self.stream = None

    def crossfade(self, s1: np.ndarray, s2: np.ndarray) -> np.ndarray:
        fade_len = min(len(s1), len(s2), self.fade_samples)
        fade = np.linspace(0, 1, fade_len)
        result = np.empty(len(s1), dtype=np.float32)
        result[:-fade_len] = s1[:-fade_len]
        result[-fade_len:] = (s1[-fade_len:] * (1 - fade)) + (s2[:fade_len] * fade)
        return result

    def create_stream(self):
        return sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype=np.float32, 
                             blocksize=self.buffer_size)

    def write_wav(self, data: np.ndarray, filename: str):
        with wave.open(filename, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(self.sample_rate)
            f.writeframes((data * 32767).astype(np.int16).tobytes())

class FormulaEngine:
    def __init__(self):
        self.globals = {}
        self.cache = {}
        self.phases = {}

    def update_globals(self, code: str):
        self.globals.clear()
        self.cache.clear()

        try:
            # Give formulas access to phase tracking and time
            global_namespace = {
                'get_phase': self.get_phase, 
                'set_phase': self.set_phase,
                't': 0  # Initialize t
            }
            exec(code, global_namespace, global_namespace)

            self.globals.update(global_namespace)
            self.globals['math'] = math
            self.globals['np'] = np

        except Exception as e:
            print(f"Error updating globals: {e}")

    def get_phase(self, name: str) -> float:
        return self.phases.get(name, 0.0)

    def reset_phases(self):
        self.phases.clear()

    def set_phase(self, name: str, value: float):
        self.phases[name] = value % 1

    def generate_samples(self, formula: str, t_start: int, num_samples: int, vars_dict: Dict) -> np.ndarray:
        if not formula.strip(): 
            return np.zeros(num_samples, dtype=np.float32)
        try:
            t = np.linspace(t_start, t_start + num_samples - 1, num_samples, dtype=np.float32)
            # Update t in globals before executing formula
            self.globals['t'] = t
            local_vars = {**self.globals, **vars_dict, 't': t}

            numpy_formula = formula.replace('math.', 'np.')

            exec(numpy_formula, self.globals, local_vars)            
            # Replace scalar math functions with numpy equivalents
            numpy_formula = formula.replace('math.', 'np.')

            exec(numpy_formula, self.globals, local_vars)

            result = local_vars.get('output', np.zeros(num_samples))
            return np.asarray(result, dtype=np.float32)

        except Exception as e:
            print(f"Vectorized formula error: {e}")
            return np.zeros(num_samples, dtype=np.float32)

    def eval_formula(self, formula:str, t: float, vars_dict: Dict) -> float:
        if not formula.strip(): 
            return 0
        try:
            # Update t in globals before executing formula
            self.globals['t'] = t
            local_vars = {**self.globals, **vars_dict, 't': t}
            exec(formula, self.globals, local_vars)
            return local_vars.get('output', 0)
        except Exception as e:
            print(f"Formula error: {e}")
            return 0
    
class Grid:
    def __init__(self, parent: ttk.Frame):
        self.parent = parent
        self.grid_frame = parent
        self.cells = []
        self.current_row = 0
        self.current_col = 0
        self.editing = False
        self.column_vars = {}
        self.num_columns = 32
        self.cell_width = 4
        
        # Create container frame for all grid elements
        self.container = ttk.Frame(parent)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Create preview/edit box above grid
        self.preview_frame = ttk.LabelFrame(self.container, text="Cell Content", padding=5)
        self.preview_frame.pack(fill=tk.X, pady=(0, 5))
        
        preview_container = ttk.Frame(self.preview_frame)
        preview_container.pack(fill=tk.X, expand=True)
        
        self.preview_text = ttk.Entry(preview_container)
        self.preview_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Create indicator in the preview container
        self.indicator = tk.Frame(preview_container, width=4, height=4, background="#69db7c")
        self.indicator.pack(side=tk.LEFT, padx=(5, 0))
        
        # Bind preview box changes to update cell content
        self.preview_text.bind('<Return>', self.finish_editing)
        self.preview_text.bind('<FocusOut>', self.finish_editing)
        
        # Add key bindings for editing mode
        self.preview_text.bind('<Key>', self.handle_edit_keypress)
        self.preview_text.bind('<Button-1>', self.enter_edit_mode)
        
        # Create grid frame
        self.grid_frame = ttk.Frame(self.container)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)

        # Add column headers
        for i in range(self.num_columns):
            ttk.Label(self.grid_frame, text=str(i+1), width=self.cell_width).grid(row=0, column=i, padx=1, pady=1)

    def enter_edit_mode(self, event=None):
        """Enter edit mode (red) when preview text is clicked"""
        if not self.editing:
            self.editing = True
            self.show_indicator()
            self.preview_text.focus_set()
            # Don't set cursor position - let it be freely movable in red mode

    def handle_edit_keypress(self, event):
        """Handle keypress events in red mode"""
        if self.editing:
            # Schedule update after the key event is processed
            self.preview_text.after(1, self.update_cell_from_preview)
            if event.keysym == 'Return':
                self.finish_editing()
                return "break"
            return None

    def interpret_cell_value(self, value: str) -> str:
        """Convert cell value to its variable assignment form without modifying display"""
        if not value:
            return value
            
        # Handle {var} notation
        var_match = re.match(r'^{(\w+)}$', value.strip())
        if var_match:
            return value  # Keep display as is, just store the variable name
            
        # Handle {var1,var2} notation for multiple variables
        multi_var_match = re.match(r'^{([\w,]+)}$', value.strip())
        if multi_var_match:
            return value  # Keep display as is
            
        # If we have variables defined for this column
        if self.current_col in self.column_vars:
            vars = self.column_vars[self.current_col]
            if isinstance(vars, list):
                # Handle multiple variables
                values = value.split(',')
                if len(values) == len(vars):
                    return value  # Keep comma-separated values as is
            else:
                # Handle single variable
                return value  # Keep the raw value
                
        return value

    def update_cell_from_preview(self):
        """Update the current cell content from the preview box while editing"""
        if self.editing and hasattr(self, 'current_cell'):
            new_value = self.preview_text.get()
            self.current_cell.delete(0, tk.END)
            self.current_cell.insert(0, new_value)
            self._on_cell_edit(self.current_row, self.current_col)

    def _sync_preview_with_cell(self, event=None):
        """Sync preview text with current cell content"""
        if hasattr(self, 'current_cell'):
            self.preview_text.delete(0, tk.END)
            self.preview_text.insert(0, self.current_cell.get())

    def get_playback_value(self, value: str, col: int) -> str:
        """Convert display value to the format needed for playback"""
        if not value:
            return value
            
        # Handle {var} notation
        var_match = re.match(r'^{(\w+)}$', value.strip())
        if var_match:
            var_name = var_match.group(1)
            return f"{var_name} = {value}"  # Convert to assignment during playback
            
        # Handle {var1,var2} notation
        multi_var_match = re.match(r'^{([\w,]+)}$', value.strip())
        if multi_var_match:
            vars = multi_var_match.group(1).split(',')
            self.column_vars[col] = vars
            return value
            
        # If we have variables defined for this column
        if col in self.column_vars:
            vars = self.column_vars[col]
            if isinstance(vars, list):
                # Handle multiple variables
                values = value.split(',')
                if len(values) == len(vars):
                    return ';'.join(f"{var}={val.strip()}" for var, val in zip(vars, values))
            else:
                # Handle single variable
                return f"{vars}={value.strip()}"
                
        return value

    def get_values(self) -> List[List[str]]:
        """Get raw values for saving/loading"""
        return [[cell.get() for cell in row] for row in self.cells]


    def get_playback_values(self) -> List[List[str]]:
        """Get values converted to playback format"""
        result = []
        for row in self.cells:
            row_values = []
            for col, cell in enumerate(row):
                value = cell.get().strip()
                if value:
                    # Handle {var} notation
                    var_match = re.match(r'^{(\w+)}$', value)
                    if var_match:
                        var_name = var_match.group(1)
                        self.column_vars[col] = var_name
                        row_values.append("")  # Skip this cell in playback
                        continue
    
                    # Handle specific variables that need special treatment"""
                    if col in self.column_vars:
                        var_name = self.column_vars[col]
    
                        # Handle compound operators"""
                        compound_match = re.match(r'^([+-/*])=(\d+.?\d*)$', value)
                        if compound_match:
                            op, num = compound_match.groups()
                            row_values.append(f"{var_name} = {var_name} {op} {num}")
                        else:
                            # Handle speed variable specially
                            if var_name == 'speed':
                                try:
                                    speed_val = float(value)
                                    row_values.append(f"speed = {speed_val}")
                                except ValueError:
                                    row_values.append("")
                            else:
    
                            # Handle normal assignment
                                row_values.append(f"{var_name} = {value}")
                    else:
                        row_values.append(value)  # Default case: use value as-is
                else:
                    row_values.append("")
            result.append(row_values)
        return result

    def show_indicator(self):
        """Update indicator color based on edit mode"""
        self.indicator.configure(background="#ff6b6b" if self.editing else "#69db7c")

    def hide_indicator(self, event=None):
        """No longer needed since indicator is fixed in position"""
        pass

    def cell_focused(self, row: int, col: int):
        """Handle cell focus events and exit edit mode"""
        if 0 <= row < len(self.cells) and 0 <= col < self.num_columns:
            self.editing = False  # Exit edit mode when clicking grid
            self.current_row = row
            self.current_col = col
            self.show_cell_content(self.cells[row][col])
            self.show_indicator()

    def show_cell_content(self, cell):
        """Update preview box with cell content without changing focus"""
        self.current_cell = cell
        if self.editing:
            return  # Don't update preview content while in edit mode
        self.preview_text.delete(0, tk.END)
        self.preview_text.insert(0, cell.get())

    def handle_keypress(self, event):
        """Handle key events in green mode"""
        if self.editing:
            return None
            
        if event.keysym in ('Up', 'Down', 'Left', 'Right'):
            # Always move to adjacent cell in green mode
            delta_row = -1 if event.keysym == 'Up' else 1 if event.keysym == 'Down' else 0
            delta_col = -1 if event.keysym == 'Left' else 1 if event.keysym == 'Right' else 0
            self.move_focus(delta_row, delta_col)
            return "break"
            
        return None

    def handle_return(self, event):
        """Handle Return key press"""
        if not self.editing:
            # Enter edit mode
            self.editing = True
            self.show_indicator()
            self.preview_text.focus_set()  # Move focus to preview text
            self.preview_text.icursor(len(self.preview_text.get()))  # Move cursor to end
        else:
            self.finish_editing(event)
        return "break"

    def finish_editing(self, event=None):
        """Exit edit mode and update cell content"""
        if self.editing and hasattr(self, 'current_cell'):
            # Store cursor position before switching to green mode
            self.last_cursor_pos = self.preview_text.index(tk.INSERT)
            
            new_value = self.preview_text.get()
            self.current_cell.delete(0, tk.END)
            self.current_cell.insert(0, new_value)
            self._on_cell_edit(self.current_row, self.current_col)
            self.editing = False
            self.show_indicator()
            # Move focus back to grid with cursor at stored position
            self.cells[self.current_row][self.current_col].focus_set()
            self.cells[self.current_row][self.current_col].icursor(
                int(self.last_cursor_pos) if hasattr(self, 'last_cursor_pos') else tk.END
            )

    def handle_tab(self, event):
        """Handle Tab key for horizontal navigation"""
        if not self.editing:
            self.move_focus(0, 1)
            return "break"

    def handle_shift_tab(self, event):
        """Handle Shift+Tab key for reverse horizontal navigation"""
        if not self.editing:
            self.move_focus(0, -1)
            return "break"

    def move_focus(self, row_delta: int, col_delta: int):
        """Move focus to another cell with bounds checking"""
        if self.editing:
            return
            
        new_row = max(0, min(self.current_row + row_delta, len(self.cells) - 1))
        new_col = max(0, min(self.current_col + col_delta, self.num_columns - 1))
        
        if new_row != self.current_row or new_col != self.current_col:
            self.current_row = new_row
            self.current_col = new_col
            self.cells[new_row][new_col].focus_set()
            # Use last known cursor position or end of cell
            self.cells[new_row][new_col].icursor(
                int(self.last_cursor_pos) if hasattr(self, 'last_cursor_pos') else tk.END
            )
            self.show_cell_content(self.cells[new_row][new_col])

    def update(self, rows: int, existing: List[List[str]] = None):
        """Update grid with proper handling of 32 columns"""
        # Default first row with extended columns
        defaults = ["{x}", "{v}", "{speed}"] + [""] * (self.num_columns - 3)
        
        # Store current focus position if any cell is focused
        focused = self.grid_frame.focus_get()
        was_focused = isinstance(focused, ttk.Entry) and focused in [cell for row in self.cells for cell in row]
        
        # Destroy excess rows if reducing row count
        while len(self.cells) > rows:
            for cell in self.cells[-1]:
                cell.destroy()
            self.cells.pop()

        # Update existing or create new rows as needed
        if len(self.cells) < rows:
            for r in range(len(self.cells), rows):
                row = []
                for c in range(self.num_columns):
                    cell = ttk.Entry(self.grid_frame, width=self.cell_width)
                    cell.grid(row=r+1, column=c, padx=1, pady=1)
                    
                    if existing and r < len(existing) and c < len(existing[r]):
                        cell.insert(0, existing[r][c])
                    elif r == 0:
                        cell.insert(0, defaults[c])
                    
                    # Add bindings
                    cell.bind('<FocusIn>', lambda e, r=r, c=c: self.cell_focused(r, c))
                    cell.bind('<Return>', self.handle_return)
                    cell.bind('<KeyPress>', self.handle_keypress)
                    cell.bind('<Tab>', self.handle_tab)
                    cell.bind('<Shift-Tab>', self.handle_shift_tab)
                    cell.bind('<KeyRelease>', lambda e, r=r, c=c: self._on_cell_edit(r, c))
                    
                    row.append(cell)
                self.cells.append(row)

        # Restore focus if needed
        if was_focused:
            self.current_row = min(self.current_row, len(self.cells)-1)
            self.current_col = min(self.current_col, self.num_columns-1)
            self.cells[self.current_row][self.current_col].focus_set()

    def _on_cell_edit(self, row: int, col: int):
        """Process cell edits and update preview"""
        if not self.cells[row][col]:
            return
            
        value = self.cells[row][col].get().strip()
        
        # Handle variable declarations
        var_match = re.match(r'^{(\w+)}$', value)
        if var_match:
            var_name = var_match.group(1)
            self.column_vars[col] = var_name
        
        # Update preview text if this is the current cell
        if row == self.current_row and col == self.current_col:
            self.preview_text.delete(0, tk.END)
            self.preview_text.insert(0, value)
        
        # Trigger grid edit callback if it exists
        if hasattr(self.parent, 'on_grid_edit') and callable(self.parent.on_grid_edit):
            self.parent.on_grid_edit()

class PatternManager:

    def __init__(self, max_patterns=100):
        self.max_patterns = max_patterns
        self.patterns = {}  # Store patterns by number
        self.order_list = []  # List to track play order
    
        # Initialize first pattern with proper column count
        blank_row = [""] * 12  # Match Grid's num_columns
        
        # Pattern 1 is special with default values
        self.patterns[1] = {
            'name': 'Initial Pattern',
            'data': [
                ["x = 0", "v = 0.25", "f = 440"] + [""] * 9,  # First row with defaults
                *[blank_row.copy() for _ in range(63)]  # Rest of the 64 rows
            ]
        }
    
        # Initialize patterns 2-12 as blank
        for i in range(2, 13):
            self.patterns[i] = {
                'name': f'Pattern {i}',
                'data': [blank_row.copy() for _ in range(64)]
            }

class PatternUI:
    def __init__(self, parent, tracker):
        self.grid_frame = parent
        self.tracker = tracker
        self.pattern_manager = PatternManager()
        
        # Current pattern tracking
        self.current_pattern_number = tk.StringVar(value="1")
 
        # Create and setup pattern UI elements
        self._create_pattern_frame()
        
    def _format_pattern_display(self, pattern_num):
        """Format pattern number and name for display"""
        pattern = self.pattern_manager.patterns.get(pattern_num)
        if isinstance(pattern, dict):
            pattern_name = pattern.get('name', f'Pattern {pattern_num}')
        else:
            pattern_name = f'Pattern {pattern_num}'
        return f"{pattern_num}: {pattern_name}"
        
    def _create_pattern_frame(self):
        """Create the complete pattern frame with all controls"""
        # Pattern controls frame
        self.pattern_frame = ttk.LabelFrame(self.grid_frame, text="Patterns", padding=5)
        self.pattern_frame.pack(fill=tk.X, pady=(0, 10))

        # Add Ctrl+S binding for saving pattern
        self.grid_frame.bind('<Control-s>', lambda e: self._save_current_pattern())

        # Pattern number selection
        self._create_pattern_number_controls()
        
        # Play order list
        self._create_play_order_controls()

    def _create_pattern_number_controls(self):
        """Create controls for pattern number selection and naming"""
        pattern_num_frame = ttk.Frame(self.pattern_frame)
        pattern_num_frame.pack(side=tk.LEFT, padx=(0, 10))
    
        ttk.Label(pattern_num_frame, text="Pattern #:").pack(side=tk.LEFT)
    
        # Pattern number entry
        self.pattern_num_entry = ttk.Entry(
            pattern_num_frame, 
            width=5, 
            textvariable=self.current_pattern_number
        )
        self.pattern_num_entry.pack(side=tk.LEFT, padx=2)
    
        # Pattern name entry
        ttk.Label(pattern_num_frame, text="Name:").pack(side=tk.LEFT, padx=(5, 0))
        self.pattern_name_entry = ttk.Entry(pattern_num_frame, width=20)
        self.pattern_name_entry.pack(side=tk.LEFT, padx=2)
    
        # Bind pattern number change events
        self.current_pattern_number.trace_add('write', self._on_pattern_number_change)
    
        # Save pattern button (only needed for new patterns now)
        ttk.Button(
            pattern_num_frame, 
            text="Save New", 
            command=self._save_current_pattern
        ).pack(side=tk.LEFT, padx=2)

    def _create_play_order_controls(self):
        """Create controls for managing play order"""
        # Play order frame
        order_frame = ttk.Frame(self.pattern_frame)
        order_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        ttk.Label(order_frame, text="Play Order:").pack(side=tk.LEFT)
        
        # Listbox for play order
        self.order_listbox = tk.Listbox(order_frame, height=3, width=20)
        self.order_listbox.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.order_listbox.bind('<Double-1>', self._load_selected_pattern)        

        # Buttons frame
        buttons_frame = ttk.Frame(order_frame)
        buttons_frame.pack(side=tk.LEFT)
        
        # Add pattern to order
        ttk.Button(
            buttons_frame, 
            text="+", 
            width=2,
            command=self._show_pattern_selection
        ).pack(pady=2)
        
        # Remove pattern from order
        ttk.Button(
            buttons_frame, 
            text="-", 
            width=2,
            command=self._remove_pattern_from_order
        ).pack(pady=2)
    
        # Add these lines at the end:
        self.pattern_manager.order_list.append(1)
        self.order_listbox.insert(tk.END, "1: Initial Pattern")

    def _on_pattern_number_change(self, *args):
        """Update tracker view when pattern number changes"""
        try:
            pattern_num = int(self.current_pattern_number.get())
            
            if pattern_num not in self.pattern_manager.patterns:
                return
            
            pattern = self.pattern_manager.patterns[pattern_num]
            pattern_data = pattern['data']
            pattern_name = pattern.get('name', f'Pattern {pattern_num}')
            
            # Update pattern name entry
            self.pattern_name_entry.delete(0, tk.END)
            self.pattern_name_entry.insert(0, pattern_name)
            
            # Store current pattern data
            if hasattr(self, '_previous_pattern'):
                try:
                    old_pattern_num = int(self._previous_pattern)
                    if old_pattern_num in self.pattern_manager.patterns:
                        self.pattern_manager.patterns[old_pattern_num]['data'] = self.tracker.grid.get_values()
                except ValueError:
                    pass
            
            # Update grid with new pattern data
            self.tracker.rows_entry.delete(0, tk.END)
            self.tracker.rows_entry.insert(0, str(len(pattern_data)))
            
            for row_idx, row_data in enumerate(pattern_data):
                if row_idx < len(self.tracker.grid.cells):
                    for col_idx, cell_value in enumerate(row_data):
                        if col_idx < len(self.tracker.grid.cells[row_idx]):
                            cell = self.tracker.grid.cells[row_idx][col_idx]
                            cell.delete(0, tk.END)
                            cell.insert(0, cell_value)
            
            # Setup auto-save and update tracker
            self.tracker.grid.parent.on_grid_edit = self._auto_save_pattern
            self._previous_pattern = str(pattern_num)
            self.tracker.update_grid()
            
        except ValueError:
            pass
    
    def _auto_save_pattern(self):
        """Automatically save changes to current pattern"""
        try:
            pattern_num = int(self.current_pattern_number.get())
            if pattern_num in self.pattern_manager.patterns:
                # Get current grid data
                current_data = self.tracker.grid.get_values()
                
                # If this pattern has more stored rows than currently visible,
                # preserve the data beyond visible rows
                pattern = self.pattern_manager.patterns[pattern_num]
                if isinstance(pattern, dict) and len(pattern['data']) > len(current_data):
                    preserved_data = pattern['data'][len(current_data):]
                    current_data.extend(preserved_data)
                
                self.pattern_manager.patterns[pattern_num]['data'] = current_data
        except ValueError:
            pass

    def _save_current_pattern(self):
        """Save current grid as a new pattern"""
        try:
            pattern_num = int(self.current_pattern_number.get())
            if pattern_num <= 0:
                raise ValueError("Pattern number must be positive")
            
            # Get pattern name
            pattern_name = self.pattern_name_entry.get().strip() or f"Pattern {pattern_num}"
            
            # Save pattern with name
            self.pattern_manager.patterns[pattern_num] = {
                'name': pattern_name,
                'data': self.tracker.grid.get_values()
            }
            
            # Setup auto-save for future edits
            self.tracker.grid.parent.on_grid_edit = self._auto_save_pattern
            
            # Update pattern indicator
            self._update_pattern_indicator()
            
            messagebox.showinfo("Pattern Saved", f"Pattern {pattern_num} saved successfully")
        
        except ValueError:
            messagebox.showerror("Invalid Pattern Number", "Please enter a valid positive integer")

    def _show_pattern_selection(self):
        """Show dialog to select and add pattern to play order"""
        available_patterns = list(self.pattern_manager.patterns.keys())
        
        if not available_patterns:
            messagebox.showwarning("No Patterns", "No patterns have been created yet!")
            return
        
        select_window = tk.Toplevel(self.grid_frame)
        select_window.title("Select Pattern")
        select_window.geometry("300x400")
        
        pattern_listbox = tk.Listbox(select_window, width=50)
        pattern_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Populate listbox with pattern numbers and names
        for pattern_num in available_patterns:
            pattern_listbox.insert(tk.END, self._format_pattern_display(pattern_num))
    
        def _add_selected_pattern():
            try:
                selection = pattern_listbox.curselection()[0]
                pattern_num = available_patterns[selection]
                
                self.pattern_manager.order_list.append(pattern_num)
                self.order_listbox.insert(tk.END, self._format_pattern_display(pattern_num))
                
                select_window.destroy()
            except IndexError:
                messagebox.showwarning("No Selection", "Please select a pattern")
        
        # Add buttons
        button_frame = ttk.Frame(select_window)
        button_frame.pack(pady=10)
        
        ttk.Button(
            button_frame, 
            text="Add to Play Order", 
            command=_add_selected_pattern
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Cancel", 
            command=select_window.destroy
        ).pack(side=tk.LEFT)


    def _load_selected_pattern(self, event):
        """Load the selected pattern from play order"""
        try:
            index = self.order_listbox.curselection()[0]
            pattern_text = self.order_listbox.get(index)
            pattern_num = int(pattern_text.split(':')[0])  # Extract pattern number from display text
            
            self.current_pattern_number.set(str(pattern_num))
        
        except (IndexError, ValueError) as e:
            messagebox.showwarning("No Selection", "Select a pattern to load")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load pattern: {e}")

    def _remove_pattern_from_order(self):
        """Remove selected pattern from play order"""
        try:
            index = self.order_listbox.curselection()[0]
            
            self.order_listbox.delete(index)
            del self.pattern_manager.order_list[index]
        
        except IndexError:
            messagebox.showwarning("No Selection", "Select a pattern to remove")

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
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup_and_close)
        self.root.bind('<F5>', lambda e: self.toggle_play())
        self.grid_frame.bind('<F5>', lambda e: self.toggle_play())


    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
    
        # Top section (fixed)
        self.top_frame = ttk.Frame(main_frame)
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)
    
        # Global variables section - Now in a popup
        globals_frame = ttk.Frame(self.top_frame)
        globals_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(globals_frame, text="Edit Global Variables", command=self.show_globals_dialog).pack()
    
        # Initialize globals_text as hidden widget to store content
        self.globals_text = tk.Text(globals_frame)
        self.globals_text.pack_forget()  # Hide it
        self.globals_text.insert("1.0", """# Basic system variables
s = 44100  # sample rate
f = 432    # base frequency

import numpy as np

# Basic waveforms with phase offset support
def sine(p, v): 
    return np.sin((p * f / s) * np.pi) * v

def saw(p, v):
    return ((p/2 * f / s + 0.5) % 1 * 2 - 1) * v

def sq(p, v, duty=0.5):
    return (((p * f / s) % 1 < duty) * 2 - 1) * v

def tri(p, v):
    return (2 * abs(2 * ((p * f / s) % 1 - 0.5)) - 1) * v

def noise(v):
    return (np.random.random() * 2 - 1) * v

# Dictionary mapping pitch classes to semitone numbers
NOTE_TO_SEMITONE = {
    'C': 0, 'C#': 1, 'Db': 1,
    'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4,
    'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11
}

def note_to_freq(note, octave=4, cents=0):

    # Convert note to semitone number
    if note.upper() not in NOTE_TO_SEMITONE:
        raise ValueError(f"Invalid note: {note}")
        
    semitone = NOTE_TO_SEMITONE[note.upper()]
    
    # Calculate total semitones from A4 (including octave)
    semitones_from_a4 = semitone - NOTE_TO_SEMITONE['A'] + (octave - 4) * 12
    
    # Add cents offset (100 cents = 1 semitone)
    total_semitones = semitones_from_a4 + cents/100
    
    # Convert to frequency ratio (each semitone is 2^(1/12))
    return 2 ** (total_semitones/12)

# Frequency helpers
def cents(c): return 2**(c/12)
def ratio(r): return 2**(np.log2(r))
def hz_to_phase(hz): return hz/s

# Modulation and effects
def plain(wave_func, p, v):
    return wave_func(p, v)

def vibrato(wave_func, p, v, rate=5, depth=0.1):
    # Calculate delta time between samples
    dp = p - np.roll(p, 1)
    dp[0] = dp[1]  # Fix first sample
    
    # Accumulate phase with modulated time
    mod = depth * np.sin(2 * np.pi * rate * p/s)
    phase = np.cumsum(dp * (1 + mod))
    
    return wave_func(phase, v)

def trill(wave_func, p, v, rate=5, depth=0.1):
    # Calculate delta time between samples
    dp = p - np.roll(p, 1)
    dp[0] = dp[1]  # Fix first sample
    
    # Square wave modulation instead of sine
    mod = depth * ((np.sin(2 * np.pi * rate * p/s) > 0) * 2 - 1)
    phase = np.cumsum(dp * (1 + mod))
    
    return wave_func(phase, v)

def tremolo(wave_func, p, v, rate=5, depth=0.3):
    dp = p - np.roll(p, 1)
    dp[0] = dp[1]  # Fix first sample
    phase = np.cumsum(dp)  # Maintain original phase
    mod = 1 + depth * np.sin(2 * np.pi * rate * p/s)
    return wave_func(phase, v * mod)

def pitch_down(wave_func, p, v, speed=0.1):
    dp = p - np.roll(p, 1)
    dp[0] = dp[1]
    # Create linear downward pitch ramp
    mod = 1.0 - (speed * p/s)
    phase = np.cumsum(dp * mod)
    return wave_func(phase, v)

def pitch_up(wave_func, p, v, speed=0.1):
    dp = p - np.roll(p, 1)
    dp[0] = dp[1]
    # Create linear upward pitch ramp
    mod = 1.0 + (speed * p/s)
    phase = np.cumsum(dp * mod)
    return wave_func(phase, v)

def portamento(wave_func, p, v, target=2.0, speed=0.1):
    dp = p - np.roll(p, 1)
    dp[0] = dp[1]
    # Smooth transition using exponential approach
    mod = 1.0 + (target - 1.0) * (1.0 - np.exp(-speed * p/s))
    phase = np.cumsum(dp * mod)
    return wave_func(phase, v)

def fm(carrier_p, mod_p, v, mod_depth=1):
    return sine(carrier_p + mod_depth * sine(mod_p, 1), v)

# ADSR envelope
def adsr(t, a=0.1, d=0.1, s=0.7, r=0.2, gate_time=1.0):
    if t < a:  # Attack
        return t/a
    elif t < a + d:  # Decay
        return 1.0 - (1.0-s)*(t-a)/d
    elif t < gate_time:  # Sustain
        return s
    elif t < gate_time + r:  # Release
        return s * (1.0 - (t-gate_time)/r)
    return 0.0

# Utility mixers and routers
def mix(*signals, weights=None):
    if weights is None:
        weights = [1.0/len(signals)] * len(signals)
    return sum(s * w for s, w in zip(signals, weights))
""")
   
        # Output formula section
        formula_frame = ttk.LabelFrame(self.top_frame, text="Output Formula", padding=5)
        formula_frame.pack(fill=tk.X, pady=(0, 10))
        self.formula_text = tk.Text(formula_frame, height=3)
        self.formula_text.pack(fill=tk.X)
        self.formula_text.insert("1.0", "output = vibrato(saw,cents(x)*t,v,r,d)")
    
        grid_controls = ttk.Frame(self.top_frame)
        grid_controls.pack(fill=tk.X, pady=5)
        
        # Rows control
        rows_frame = ttk.Frame(grid_controls)
        rows_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(rows_frame, text="Rows:").pack(side=tk.LEFT)
        self.rows_entry = ttk.Entry(rows_frame, width=5)
        self.rows_entry.pack(side=tk.LEFT, padx=2)
        self.rows_entry.insert(0, "64")
        
        # Default Speed control
        speed_frame = ttk.Frame(grid_controls)
        speed_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(speed_frame, text="Default Speed (rows/sec):").pack(side=tk.LEFT)
        self.speed_entry = ttk.Entry(speed_frame, width=5)
        self.speed_entry.pack(side=tk.LEFT, padx=2)
        self.speed_entry.insert(0, "4")
        
        # Help button for speed
        help_text = ("Speed Control Help:\n\n"
                    "1. Default speed is set above and applies to all rows\n"
                    "2. To change speed for a specific row, add 'speed = X' to any cell in that row\n"
                    "3. Examples:\n"
                    "   speed = 1    # one row per second\n"
                    "   speed = 4    # four rows per second\n"
                    "   speed = 0.5  # two seconds per row\n"
                    "4. Speed changes take effect at the start of each row")
        
        def show_help():
            messagebox.showinfo("Speed Control Help", help_text)
            
        ttk.Button(speed_frame, text="?", width=2, command=show_help).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(grid_controls, text="Update Grid", command=self.update_grid).pack(side=tk.LEFT)
    
        # Create a frame for the scrollable area
        scroll_frame = ttk.Frame(main_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10)
    
        # Add vertical scrollbar
        v_scrollbar = ttk.Scrollbar(scroll_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
        # Add horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    
        # Create canvas for scrolling
        self.canvas = tk.Canvas(scroll_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        # Configure scrollbars
        v_scrollbar.configure(command=self.canvas.yview)
        h_scrollbar.configure(command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set,
                             xscrollcommand=h_scrollbar.set)
    
        # Create frame for grid inside canvas
        self.grid_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor='nw')
    
        # Create Grid in the scrollable frame
        self.grid = Grid(self.grid_frame)
        
        # Update scroll region when grid frame changes
        self.grid_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
    
        # Replace pattern management with new PatternUI
        self.pattern_ui = PatternUI(self.top_frame, self)

        # Explicitly set to Pattern 1 on startup
        self.pattern_ui.current_pattern_number.set("1")
        
        # Bottom controls (fixed at bottom)
        controls = ttk.Frame(main_frame)
        controls.pack(fill=tk.X, padx=10, pady=10, side=tk.BOTTOM)
        self.play_button = ttk.Button(controls, text="Play", command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="Export WAV", command=self.export_wav).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="Save", command=self.save).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="Load", command=self.load).pack(side=tk.LEFT, padx=2)
    
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Initial grid update
        self.update_grid()
    
    def get_samples_per_row(self) -> int:
        """Calculate samples per row based on speed setting"""
        try:
            speed = float(self.speed_entry.get())
            if speed <= 0:
                speed = 1
                self.speed_entry.delete(0, tk.END)
                self.speed_entry.insert(0, "1")
            return int(self.audio.sample_rate / speed)
        except (ValueError, ZeroDivisionError):
            self.speed_entry.delete(0, tk.END)
            self.speed_entry.insert(0, "4")
            return int(self.audio.sample_rate / 4)

    def on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """When canvas is resized, resize the inner frame to match"""
        self.canvas.itemconfig(self.canvas.find_withtag('all')[0], width=event.width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def update_grid(self):
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

    def show_globals_dialog(self):
        """Show global variables in a popup dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Global Variables")
        dialog.geometry("600x400")
        
        text = tk.Text(dialog, height=20)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # If we already have globals, load them
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

    def get_row_speed(self, vars_dict: Dict) -> float:
        """Get speed from variables dictionary, letting Python handle the math"""
        try:
            if 'speed' in vars_dict:
                return max(0.1, float(vars_dict['speed']))
        except (ValueError, TypeError):
            pass
        return float(self.speed_entry.get() or 4)
        
    def generate_audio(self, samples_per_row=None):
        buffer = np.array([], dtype=np.float32)
        current_t = self.last_t
    
        # Collect all possible variables from all sources
        all_variables = set()
        
        # From formula
        formula_text = self.formula_text.get("1.0", tk.END)
        all_variables.update(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', formula_text))
        
        # From globals
        globals_text = self.globals_text.get("1.0", tk.END)
        all_variables.update(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', globals_text))
        
        # From curly braces in grid
        for row in self.grid.cells:
            for cell in row:
                value = cell.get().strip()
                var_match = re.match(r'^{(\w+)}$', value)
                if var_match:
                    all_variables.add(var_match.group(1))
    
        # Initialize persistent vars with defaults
        persistent_vars_dict = {var: 0 for var in all_variables}
        persistent_vars_dict.update(self.formula.globals)
        persistent_vars_dict['speed'] = float(self.speed_entry.get() or 4)
    
        for pattern_num in self.pattern_ui.pattern_manager.order_list:
            if not self.is_playing and samples_per_row is None or self._stop.is_set():
                break
    
            pattern = self.pattern_ui.pattern_manager.patterns[pattern_num]
            playback_data = self.grid.get_playback_values()
    
            for row_idx, row in enumerate(playback_data):
                # Start with previous row's variables
                row_vars_dict = persistent_vars_dict.copy()
    
                """Only update variables that are explicitly set in this row"""
                has_updates = False
                for col_idx, cell_value in enumerate(row):
                    if cell_value.strip():  # Only execute non-empty cells
                        has_updates = True
                        try:
                            exec(cell_value, {}, row_vars_dict)
                        except Exception as e:
                            print(f"Error in row {row_idx}, col {col_idx}: {e}")
    
                """Update speed in persistent vars if it was modified"""
                if 'speed' in row_vars_dict:
                    persistent_vars_dict['speed'] = row_vars_dict['speed']
    
                row_speed = max(0.1, float(row_vars_dict.get('speed', persistent_vars_dict['speed'])))
    
                if samples_per_row is None:
                    row_samples = int(self.audio.sample_rate / row_speed)
                else:
                    row_samples = samples_per_row
    
                # Generate samples using persistent variables
                samples = self.formula.generate_samples(
                    self.formula_text.get("1.0", tk.END),
                    current_t,
                    row_samples,
                    persistent_vars_dict if not has_updates else row_vars_dict
                )
                current_t += row_samples
    
                # Only update persistent variables if this row had explicit updates
                if has_updates:
                    persistent_vars_dict.update(row_vars_dict)
    
                if len(buffer) == 0:
                    buffer = samples
                else:
                    buffer = self.audio.crossfade(buffer, samples)
                    buffer = np.append(buffer, samples[self.audio.fade_samples:])
    
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
            self.formula.reset_phases()  # Reset phases when stopping
        else:
            self._stop.clear()
            self.is_playing = True
            self.play_button.configure(text="Stop")
            self.formula.reset_phases()  # Reset phases when starting fresh
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

    # Update the save/load methods in MusicTracker to handle the new pattern structure:
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
                
                # Load globals and formula
                self.globals_text.delete("1.0", tk.END)
                self.globals_text.insert("1.0", state['globals'])
                self.formula_text.delete("1.0", tk.END)
                self.formula_text.insert("1.0", state['formula'])
                
                # Load rows and speed
                self.rows_entry.delete(0, tk.END)
                self.rows_entry.insert(0, state['rows'])
                self.speed_entry.delete(0, tk.END)
                self.speed_entry.insert(0, state['speed'])
                
                # Handle patterns
                patterns = state.get('patterns', {})
                # Convert string keys to integers if necessary
                patterns = {int(k): v for k, v in patterns.items()}
                
                if patterns and isinstance(next(iter(patterns.values())), list):
                    # Convert old format to new format
                    self.pattern_ui.pattern_manager.patterns = {
                        num: {'name': f'Pattern {num}', 'data': data}
                        for num, data in patterns.items()
                    }
                else:
                    self.pattern_ui.pattern_manager.patterns = patterns
                
                # Clear and restore order list
                self.pattern_ui.order_listbox.delete(0, tk.END)
                restored_order = state.get('order', [])
                self.pattern_ui.pattern_manager.order_list = restored_order
                
                # Update order listbox with pattern names
                for pattern_num in restored_order:
                    pattern = self.pattern_ui.pattern_manager.patterns[pattern_num]
                    if isinstance(pattern, dict):
                        pattern_name = pattern.get('name', f'Pattern {pattern_num}')
                    else:
                        pattern_name = f'Pattern {pattern_num}'
                    self.pattern_ui.order_listbox.insert(tk.END, f"{pattern_num}: {pattern_name}")
                
                # Set current pattern number (this will trigger pattern load)
                current_pattern = state.get('current_pattern', '1')
                self.pattern_ui.current_pattern_number.set(current_pattern)
                
                # Update grid with current pattern data
                if current_pattern:
                    pattern_num = int(current_pattern)
                    if pattern_num in self.pattern_ui.pattern_manager.patterns:
                        pattern = self.pattern_ui.pattern_manager.patterns[pattern_num]
                        if isinstance(pattern, dict):
                            self.grid.update(int(state['rows']), pattern['data'])
                        else:
                            self.grid.update(int(state['rows']), pattern)
                
                # Update formula engine globals
                self.formula.update_globals(state['globals'])
                
                messagebox.showinfo("Load Successful", "Project loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def export_wav(self):
        """Export the current sequence as a WAV file."""
        try:
            # Get save path from user
            path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav")]
            )
            if not path:
                return

            # Update globals before generating audio
            self.formula.update_globals(self.globals_text.get("1.0", tk.END))
            
            # Calculate total number of rows
            order_list = self.pattern_ui.pattern_manager.order_list
            if not order_list:
                messagebox.showerror("Error", "No patterns in play order to export")
                return
                
            # Generate audio for entire sequence with a fixed samples per row
            audio_data = self.generate_audio(samples_per_row=5000)
            
            # Write to WAV file
            self.audio.write_wav(audio_data, path)
            
            messagebox.showinfo("Success", f"Audio exported to {path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def cleanup_and_close(self):
        self._stop.set()
        self.is_playing = False
        if self.audio.stream:
            self.audio.stream.stop()
            self.audio.stream.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicTracker(root)
    root.mainloop()