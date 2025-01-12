from typing import Dict, List, Any

class PatternManager:
    def __init__(self, max_patterns=100):
        self.max_patterns = max_patterns
        self.patterns: Dict[int, Dict[str, Any]] = {}
        self.order_list: List[int] = []

        self._initialize_patterns()

    def _initialize_patterns(self):
        blank_row = [""] * 12

        # Initialize Pattern 1 with defaults
        self.patterns[1] = {
            'name': 'Initial Pattern',
            'data': [
                ["x = 0", "v = 0.25", "f = 440"] + [""] * 9,
                *[blank_row.copy() for _ in range(63)]
            ]
        }

        # Initialize patterns 2-12 as blank
        for i in range(2, 13):
            self.patterns[i] = {
                'name': f'Pattern {i}',
                'data': [blank_row.copy() for _ in range(64)]
            }