# Holysaw

A music tracker that lets you create music using mathematical formulas.

## Features

- Create music using Python code and math
- Real-time audio playback
- Pattern-based sequencing
- Variable interpolation between rows
- Built-in waveform generators (sine, saw, square, triangle)

## Installation

Follow these steps exactly in order:

1. First, install system dependencies:

    - On macOS:
        ```bash
        brew install python tcl-tk portaudio
        ```

    - On Ubuntu/Debian:
        ```bash
        sudo apt-get update
        sudo apt-get install python3-tk portaudio19-dev python3-dev
        ```

    - On Windows:
        - Download and install Python from [python.org](https://python.org) (Tkinter included)
        - Install [PortAudio](http://www.portaudio.com/download.html)

2. Install uv (package manager):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3. Open a new terminal window (important!) and navigate to the project directory:
    ```bash
    cd path/to/holysaw
    ```

4. Create and activate a virtual environment:
    ```bash
    # Create virtual environment
    uv venv

    # On macOS/Linux:
    source .venv/bin/activate

    # On Windows:
    .venv\Scripts\activate
    ```

    After activation, your prompt should show `(.venv)` or `(.holysaw)` at the beginning.

5. Install Python packages (make sure you see (.venv) or (.holysaw) in your prompt first!):
    ```bash
    uv pip install numpy sounddevice pytest
    ```

## Running the Application

Every time you want to run the application:

1. Open a terminal and navigate to the project directory:
    ```bash
    cd path/to/holysaw
    ```

2. Activate the virtual environment:
    ```bash
    # On macOS/Linux:
    source .venv/bin/activate

    # On Windows:
    .venv\Scripts\activate
    ```
    Make sure you see `(.venv)` in your prompt!

3. Run the application:
    ```bash
    python3 main.py
    ```

## Common Installation Problems

1. If you see "No module named 'numpy'" or similar:
   - Make sure you see `(.venv)` in your terminal prompt
   - If not, activate the virtual environment (step 2 above)
   - Try reinstalling packages: `uv pip install numpy sounddevice pytest`

2. If you see "No module named 'tkinter'":
   - On macOS: Run `brew install python tcl-tk`
   - On Linux: Run `sudo apt-get install python3-tk`
   - On Windows: Reinstall Python and check "tcl/tk" during installation

3. If you hear no sound:
   - On macOS: Run `brew install portaudio`
   - On Linux: Run `sudo apt-get install portaudio19-dev`
   - On Windows: Install PortAudio from the link above

4. If the terminal doesn't recognize 'uv':
   - Open a new terminal window after installing uv
   - On Windows: Restart your terminal as Administrator

## Quick Start Guide

1. The application window has several sections:
   - **Global Variables**: Click "Edit Global Variables" to define functions and variables
   - **Output Formula**: Write the formula that generates your sound
   - **Pattern Grid**: Enter values and variable assignments
   - **Pattern Controls**: Manage patterns and playback order

2. Basic usage:
   - Press F5 or click "Play" to start/stop playback
   - Use the grid to create patterns
   - First row defines variables with `{variable_name}`
   - Other rows can assign values to these variables
   - Save your work using File > Save (saves as .json)
   - Load existing songs using File > Load

3. Example pattern:

   ```txt
   Row 1: {x}     {v}      {f}
   Row 2: 0       0.5      440
   Row 3: 0.5     0.7      880
   ```

   With formula: `output = sine(t * f, v) * x`

4. Check out `examples/demo_song.json` for a complete song that demonstrates:
   - Custom functions (arpeggiation, LFO)
   - Multiple patterns (bass, lead, pad)
   - Advanced waveform combinations
   - Variable interpolation
   - Frequency modulation

   Load it using File > Load to see how it works!

## Built-in Functions

The tracker comes with several built-in waveform generators:

- `sine(phase, volume)`: Generate a sine wave
- `saw(phase, volume)`: Generate a sawtooth wave
- `sq(phase, volume, duty=0.5)`: Generate a square wave
- `tri(phase, volume)`: Generate a triangle wave

## Tips

- Use the speed control to adjust how fast patterns play
- Variables interpolate smoothly between rows
- Combine different waveforms for complex sounds
- Use Python's math functions in your formulas
- Save your work frequently!

## Troubleshooting

If you encounter audio issues:

1. Check your system's audio settings
2. Make sure no other application is using the audio device
3. Try adjusting the buffer size if you hear crackling

For other issues:

- Make sure all dependencies are correctly installed
- Check that your Python version is 3.8 or newer
- Verify your formulas are valid Python code

## Testing

To run tests:

```bash
uv pytest src/tests
```

## License

This project is open source and available under the MIT License.

