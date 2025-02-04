import tkinter as tk
from tkinter import ttk
import re
from typing import List, Dict, Optional

class Grid:
    def __init__(self, parent: ttk.Frame, canvas: tk.Canvas):
        self.parent = parent
        self.grid_frame = parent
        self.canvas = canvas  # Store canvas reference
        self.cells: List[List[ttk.Entry]] = []
        self.current_row = 0
        self.current_col = 0
        self.editing = False
        self.column_vars: Dict[int, str] = {}
        self.num_columns = 32
        self.cell_width = 4
        self.current_cell: Optional[ttk.Entry] = None
        self._setup_ui()

    def _setup_ui(self):
        self.container = ttk.Frame(self.parent)
        self.container.pack(fill=tk.BOTH, expand=True)
        self._setup_preview_frame()
        self._setup_grid_frame()

    def _setup_preview_frame(self):
        self.preview_frame = ttk.LabelFrame(self.container, text="Cell Content", padding=5)
        self.preview_frame.pack(fill=tk.X, pady=(0, 5))

        preview_container = ttk.Frame(self.preview_frame)
        preview_container.pack(fill=tk.X, expand=True)

        self.preview_text = ttk.Entry(preview_container)
        self.preview_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.indicator = tk.Frame(preview_container, width=4, height=4, background="#69db7c")
        self.indicator.pack(side=tk.LEFT, padx=(5, 0))

        self._setup_preview_bindings()

    def _setup_preview_bindings(self):
        self.preview_text.bind('<Return>', self.finish_editing)
        self.preview_text.bind('<FocusOut>', self.finish_editing)
        self.preview_text.bind('<Key>', self.handle_edit_keypress)
        self.preview_text.bind('<Button-1>', self.enter_edit_mode)

    def _setup_grid_frame(self):
        self.grid_frame = ttk.Frame(self.container)
        self.grid_frame.pack(fill=tk.BOTH, expand=True)

        # Add column headers
        for i in range(self.num_columns):
            ttk.Label(self.grid_frame, text=str(i+1), width=self.cell_width).grid(
                row=0, column=i, padx=1, pady=1
            )

    def update(self, rows: int, existing: Optional[List[List[str]]] = None):
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

                    # Set cell value based on existing data or defaults
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

                    row.append(cell)
                self.cells.append(row)
        else:
            # Update existing rows with new values
            for r in range(len(self.cells)):
                for c in range(self.num_columns):
                    if existing and r < len(existing) and c < len(existing[r]):
                        self.cells[r][c].delete(0, tk.END)
                        self.cells[r][c].insert(0, existing[r][c])
                    elif r == 0:
                        self.cells[r][c].delete(0, tk.END)
                        self.cells[r][c].insert(0, defaults[c])

        # Restore focus if needed
        if was_focused:
            self.current_row = min(self.current_row, len(self.cells)-1)
            self.current_col = min(self.current_col, self.num_columns-1)
            self.cells[self.current_row][self.current_col].focus_set()

    def _create_cell(self, row: int, col: int) -> ttk.Entry:
        cell = ttk.Entry(self.grid_frame, width=self.cell_width)
        cell.grid(row=row+1, column=col, padx=1, pady=1)

        cell.bind('<FocusIn>', lambda e, r=row, c=col: self.cell_focused(r, c))
        cell.bind('<Return>', self.handle_return)
        cell.bind('<KeyPress>', self.handle_keypress)
        cell.bind('<Tab>', self.handle_tab)
        cell.bind('<Shift-Tab>', self.handle_shift_tab)

        return cell

    def handle_keypress(self, event):
        """Handle key events in green mode"""
        if self.editing:
            return None

        if event.keysym in ('Up', 'Down', 'Left', 'Right'):
            delta_row = -1 if event.keysym == 'Up' else 1 if event.keysym == 'Down' else 0
            delta_col = -1 if event.keysym == 'Left' else 1 if event.keysym == 'Right' else 0
            self.move_focus(delta_row, delta_col)
            return "break"

        return None

    def handle_return(self, event):
        """Handle Return key press"""
        if not self.editing:
            self.editing = True
            self.show_indicator()
            self.preview_text.focus_set()
            self.preview_text.icursor(len(self.preview_text.get()))
        else:
            self.finish_editing(event)
        return "break"

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

    def cell_focused(self, row: int, col: int):
        """Handle cell focus events and exit edit mode"""
        if 0 <= row < len(self.cells) and 0 <= col < self.num_columns:
            self.editing = False
            self.current_row = row
            self.current_col = col
            self.show_cell_content(self.cells[row][col])
            self.show_indicator()
            self.center_on_cell(row, col)  # Add this line

    def center_on_cell(self, row, col):
        self.grid_frame.update_idletasks()
        cell = self.cells[row][col]
        
        # Get cell position relative to canvas
        cell_y = cell.winfo_y()
        
        # Get canvas viewport height
        canvas_height = self.canvas.winfo_height()
        
        # Calculate position to center cell
        center_position = (cell_y - (canvas_height/2)) / self.grid_frame.winfo_height()
        
        # Move canvas to center on cell
        self.canvas.yview_moveto(max(0, min(1, center_position)))

    def enter_edit_mode(self, event=None):
        """Enter edit mode (red) when preview text is clicked"""
        if not self.editing:
            self.editing = True
            self.show_indicator()
            self.preview_text.focus_set()

    def handle_edit_keypress(self, event):
        """Handle keypress events in red mode"""
        if self.editing:
            # Don't treat cursor movement as edits
            if event.keysym in ('Left', 'Right', 'Home', 'End'):
                return None
                
            # Schedule update after other keypresses
            self.preview_text.after(1, self.update_cell_from_preview)
            
            if event.keysym == 'Return':
                self.finish_editing()
                return "break"
            return None

    def finish_editing(self, event=None):
        """Exit edit mode and update cell content"""
        if self.editing and hasattr(self, 'current_cell'):
            self.last_cursor_pos = self.preview_text.index(tk.INSERT)

            new_value = self.preview_text.get()
            self.current_cell.delete(0, tk.END)
            self.current_cell.insert(0, new_value)
            self._on_cell_edit(self.current_row, self.current_col)
            self.editing = False
            self.show_indicator()
            self.cells[self.current_row][self.current_col].focus_set()
            self.cells[self.current_row][self.current_col].icursor(
                int(self.last_cursor_pos) if hasattr(self, 'last_cursor_pos') else tk.END
            )

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
            self.cells[new_row][new_col].icursor(
                int(self.last_cursor_pos) if hasattr(self, 'last_cursor_pos') else tk.END
            )
            self.show_cell_content(self.cells[new_row][new_col])

    def show_indicator(self):
        """Update indicator color based on edit mode"""
        self.indicator.configure(background="#ff6b6b" if self.editing else "#69db7c")

    def show_cell_content(self, cell):
        """Update preview box with cell content"""
        self.current_cell = cell
        if self.editing:
            return
    
        """Store current cursor position"""
        cursor_pos = self.preview_text.index(tk.INSERT)
    
        self.preview_text.delete(0, tk.END)
        self.preview_text.insert(0, cell.get())
    
        """Restore cursor position if within bounds"""
        if cursor_pos <= len(cell.get()):
            self.preview_text.icursor(cursor_pos)


    def update_cell_from_preview(self):
        """Update the current cell content from the preview box while editing"""
        if self.editing and hasattr(self, 'current_cell'):
            # Store cursor position before update
            cursor_pos = self.preview_text.index(tk.INSERT)
            
            new_value = self.preview_text.get()
            self.current_cell.delete(0, tk.END)
            self.current_cell.insert(0, new_value)
            
            # Restore cursor position
            self.preview_text.icursor(cursor_pos)
            
            if hasattr(self.parent, 'on_grid_edit') and callable(self.parent.on_grid_edit):
                self.parent.on_grid_edit()

    def _on_cell_edit(self, row: int, col: int):
        """Process cell edits and update preview"""
        if not self.cells[row][col]:
            return
    
        value = self.cells[row][col].get().strip()
    
        var_match = re.match(r'^{(\w+)}$', value)
        if var_match:
            var_name = var_match.group(1)
            self.column_vars[col] = var_name
    
        # Update preview if this is the current cell
        if row == self.current_row and col == self.current_col:
            self.preview_text.delete(0, tk.END)
            self.preview_text.insert(0, value)
    
        # Always trigger autosave
        if hasattr(self.parent, 'on_grid_edit') and callable(self.parent.on_grid_edit):
            self.parent.on_grid_edit()

    def interpret_cell_value(self, value: str) -> str:
        """Convert cell value to its variable assignment form"""
        if not value:
            return value

        var_match = re.match(r'^{(\w+)}$', value.strip())
        if var_match:
            return value

        multi_var_match = re.match(r'^{([\w,]+)}$', value.strip())
        if multi_var_match:
            return value

        if self.current_col in self.column_vars:
            vars = self.column_vars[self.current_col]
            if isinstance(vars, list):
                values = value.split(',')
                if len(values) == len(vars):
                    return value
            else:
                return value

        return value

    def get_playback_value(self, value: str, col: int) -> str:
        """Convert display value to playback format"""
        if not value:
            return value

        var_match = re.match(r'^{(\w+)}$', value.strip())
        if var_match:
            var_name = var_match.group(1)
            return f"{var_name} = {value}"

        multi_var_match = re.match(r'^{([\w,]+)}$', value.strip())
        if multi_var_match:
            vars = multi_var_match.group(1).split(',')
            self.column_vars[col] = vars
            return value

        if col in self.column_vars:
            vars = self.column_vars[col]
            if isinstance(vars, list):
                values = value.split(',')
                if len(values) == len(vars):
                    return ';'.join(f"{var}={val.strip()}" for var, val in zip(vars, values))
            else:
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
    
                    # Handle specific variables that need special treatment
                    if col in self.column_vars:
                        var_name = self.column_vars[col]
    
                        # Handle compound operators
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