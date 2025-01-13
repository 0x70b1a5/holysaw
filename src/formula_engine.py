import numpy as np
import math
import logging

logger = logging.getLogger(__name__)

class FormulaEngine:
    def __init__(self):
        logger.info("Initializing FormulaEngine")
        self.globals = {
            'np': np,
            'math': math,
            't': 0,
        }
        self.phases = {}

    def update_globals(self, code):
        """Update the globals dictionary with new code"""
        logger.info("Updating globals")
        logger.debug(f"Code to execute:\n{code}")
        try:
            exec(code, self.globals)
            logger.debug(f"Updated globals: {list(self.globals.keys())}")
        except Exception as e:
            logger.error(f"Error updating globals: {e}", exc_info=True)

    def eval_formula(self, formula, t, vars_dict):
        """Evaluate a formula with the given variables"""
        logger.debug(f"Evaluating formula: {formula}")
        logger.debug(f"Variables: {vars_dict}")
        try:
            # Update globals with current time and variables
            self.globals.update(vars_dict)
            self.globals['t'] = t

            # Execute the formula
            local_vars = self.globals.copy()
            exec(formula, self.globals, local_vars)

            if 'output' in local_vars:
                logger.debug(f"Formula output type: {type(local_vars['output'])}")
                return local_vars['output']
            else:
                logger.warning("No output variable found in formula")
                return 0
        except Exception as e:
            logger.error(f"Error evaluating formula: {e}", exc_info=True)
            return 0

    def generate_samples(self, formula, start_t, num_samples, vars_dict=None):
        """Generate audio samples from a formula"""
        logger.info(f"Generating {num_samples} samples starting at t={start_t}")
        if vars_dict is None:
            vars_dict = {}

        try:
            # Create time array
            t = np.linspace(start_t, start_t + num_samples - 1, num_samples, dtype=np.float32)
            logger.debug(f"Time array shape: {t.shape}, range: [{t[0]}, {t[-1]}]")

            # Update globals
            self.globals.update(vars_dict)
            self.globals['t'] = t

            # Execute formula
            local_vars = self.globals.copy()
            logger.debug(f"Executing formula: {formula}")
            logger.debug(f"Available variables: {list(local_vars.keys())}")
            exec(formula, self.globals, local_vars)

            if 'output' in local_vars:
                output = local_vars['output']
                logger.debug(f"Output type: {type(output)}, shape: {output.shape if isinstance(output, np.ndarray) else 'scalar'}")
                if isinstance(output, np.ndarray):
                    return output.astype(np.float32)
                else:
                    return np.full(num_samples, float(output), dtype=np.float32)
            else:
                logger.warning("No output variable found")
                return np.zeros(num_samples, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error generating samples: {e}", exc_info=True)
            return np.zeros(num_samples, dtype=np.float32)

    def set_phase(self, name, phase):
        """Set the phase for a named oscillator"""
        logger.debug(f"Setting phase for {name}: {phase}")
        self.phases[name] = phase % 1.0

    def get_phase(self, name):
        """Get the phase for a named oscillator"""
        phase = self.phases.get(name, 0.0)
        logger.debug(f"Getting phase for {name}: {phase}")
        return phase

    def reset_phases(self):
        """Reset all oscillator phases"""
        logger.info("Resetting all phases")
        self.phases.clear()