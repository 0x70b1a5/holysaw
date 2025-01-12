import tkinter as tk
from tkinter import ttk, messagebox
from .pattern_manager import PatternManager

class PatternUI:
    def __init__(self, parent, tracker):
        self.grid_frame = parent
        self.tracker = tracker
        self.pattern_manager = PatternManager()
        self.current_pattern_number = tk.StringVar(value="1")
        self._create_pattern_frame()

    def _create_pattern_frame(self):
        self.pattern_frame = ttk.LabelFrame(self.grid_frame, text="Patterns", padding=5)
        self.pattern_frame.pack(fill=tk.X, pady=(0, 10))

        self._create_pattern_number_controls()
        self._create_play_order_controls()

    def _create_pattern_number_controls(self):
        pattern_num_frame = ttk.Frame(self.pattern_frame)
        pattern_num_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(pattern_num_frame, text="Pattern #:").pack(side=tk.LEFT)
        self.pattern_num_entry = ttk.Entry(
            pattern_num_frame,
            width=5,
            textvariable=self.current_pattern_number
        )
        self.pattern_num_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(pattern_num_frame, text="Name:").pack(side=tk.LEFT, padx=(5, 0))
        self.pattern_name_entry = ttk.Entry(pattern_num_frame, width=20)
        self.pattern_name_entry.pack(side=tk.LEFT, padx=2)

        self.current_pattern_number.trace_add('write', self._on_pattern_number_change)

        ttk.Button(
            pattern_num_frame,
            text="Save New",
            command=self._save_current_pattern
        ).pack(side=tk.LEFT, padx=2)

    def _create_play_order_controls(self):
        order_frame = ttk.Frame(self.pattern_frame)
        order_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Label(order_frame, text="Play Order:").pack(side=tk.LEFT)

        self.order_listbox = tk.Listbox(order_frame, height=3, width=20)
        self.order_listbox.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.order_listbox.bind('<Double-1>', self._load_selected_pattern)

        buttons_frame = ttk.Frame(order_frame)
        buttons_frame.pack(side=tk.LEFT)

        ttk.Button(
            buttons_frame,
            text="+",
            width=2,
            command=self._show_pattern_selection
        ).pack(pady=2)

        ttk.Button(
            buttons_frame,
            text="-",
            width=2,
            command=self._remove_pattern_from_order
        ).pack(pady=2)

        # Initialize with first pattern
        self.pattern_manager.order_list.append(1)
        self.order_listbox.insert(tk.END, "1: Initial Pattern")

    def _format_pattern_display(self, pattern_num: int) -> str:
        pattern = self.pattern_manager.patterns.get(pattern_num)
        if isinstance(pattern, dict):
            pattern_name = pattern.get('name', f'Pattern {pattern_num}')
        else:
            pattern_name = f'Pattern {pattern_num}'
        return f"{pattern_num}: {pattern_name}"

    def _on_pattern_number_change(self, *args):
        """Update tracker view when pattern number changes"""
        try:
            pattern_num = int(self.current_pattern_number.get())

            if pattern_num not in self.pattern_manager.patterns:
                return

            pattern = self.pattern_manager.patterns[pattern_num]
            pattern_data = pattern['data']
            pattern_name = pattern.get('name', f'Pattern {pattern_num}')

            self.pattern_name_entry.delete(0, tk.END)
            self.pattern_name_entry.insert(0, pattern_name)

            if hasattr(self, '_previous_pattern'):
                try:
                    old_pattern_num = int(self._previous_pattern)
                    if old_pattern_num in self.pattern_manager.patterns:
                        self.pattern_manager.patterns[old_pattern_num]['data'] = self.tracker.grid.get_values()
                except ValueError:
                    pass

            self.tracker.rows_entry.delete(0, tk.END)
            self.tracker.rows_entry.insert(0, str(len(pattern_data)))

            for row_idx, row_data in enumerate(pattern_data):
                if row_idx < len(self.tracker.grid.cells):
                    for col_idx, cell_value in enumerate(row_data):
                        if col_idx < len(self.tracker.grid.cells[row_idx]):
                            cell = self.tracker.grid.cells[row_idx][col_idx]
                            cell.delete(0, tk.END)
                            cell.insert(0, cell_value)

            self.tracker.grid.parent.on_grid_edit = self._auto_save_pattern
            self._previous_pattern = str(pattern_num)
            self.tracker.update_grid()

        except ValueError:
            pass

    def _save_current_pattern(self):
        """Save current grid as a new pattern"""
        try:
            pattern_num = int(self.current_pattern_number.get())
            if pattern_num <= 0:
                raise ValueError("Pattern number must be positive")

            pattern_name = self.pattern_name_entry.get().strip() or f"Pattern {pattern_num}"

            self.pattern_manager.patterns[pattern_num] = {
                'name': pattern_name,
                'data': self.tracker.grid.get_values()
            }

            self.tracker.grid.parent.on_grid_edit = self._auto_save_pattern
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

    def _auto_save_pattern(self):
        """Automatically save changes to current pattern"""
        try:
            pattern_num = int(self.current_pattern_number.get())
            if pattern_num in self.pattern_manager.patterns:
                current_data = self.tracker.grid.get_values()
                pattern = self.pattern_manager.patterns[pattern_num]
                if isinstance(pattern, dict) and len(pattern['data']) > len(current_data):
                    preserved_data = pattern['data'][len(current_data):]
                    current_data.extend(preserved_data)

                self.pattern_manager.patterns[pattern_num]['data'] = current_data
        except ValueError:
            pass

    def _load_selected_pattern(self, event):
        """Load the selected pattern from play order"""
        try:
            index = self.order_listbox.curselection()[0]
            pattern_text = self.order_listbox.get(index)
            pattern_num = int(pattern_text.split(':')[0])
            self.current_pattern_number.set(str(pattern_num))

        except (IndexError, ValueError):
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

    # ... [Rest of PatternUI class methods] ...