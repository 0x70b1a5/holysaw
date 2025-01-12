import numpy as np
import math
from typing import Dict, Any

class FormulaEngine:
    def __init__(self):
        self.globals: Dict[str, Any] = {}
        self.cache: Dict[str, Any] = {}
        self.phases: Dict[str, float] = {}

    def update_globals(self, code: str):
        self.globals.clear()
        self.cache.clear()

        try:
            global_namespace = {
                'get_phase': self.get_phase,
                'set_phase': self.set_phase,
                't': 0
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
            self.globals['t'] = t
            local_vars = {**self.globals, **vars_dict, 't': t}

            numpy_formula = formula.replace('math.', 'np.')
            exec(numpy_formula, self.globals, local_vars)

            result = local_vars.get('output', np.zeros(num_samples))
            return np.asarray(result, dtype=np.float32)

        except Exception as e:
            print(f"Vectorized formula error: {e}")
            return np.zeros(num_samples, dtype=np.float32)

    def eval_formula(self, formula: str, t: float, vars_dict: Dict) -> float:
        if not formula.strip():
            return 0
        try:
            self.globals['t'] = t
            local_vars = {**self.globals, **vars_dict, 't': t}
            exec(formula, self.globals, local_vars)
            return local_vars.get('output', 0)
        except Exception as e:
            print(f"Formula error: {e}")
            return 0