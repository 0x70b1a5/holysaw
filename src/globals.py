# Basic system variables
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