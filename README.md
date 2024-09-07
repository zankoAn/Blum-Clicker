# Blume-Clicker
Blume Clicker is an automated tool designed for a telegram blume game . It is built using OpenCV and NumPy and is optimized for Linux systems. This tool automatically clicks on green objects and blue ice objects appearing in the game while avoiding clicks on bombs.


## Requirements

Before running the application, make sure you have the following tools installed:

- `xdotool`
- `xwininfo`


To install the required Python packages, run:

    pip install -r requirements.txt

## Usage

1. Start the ‍**Blume** game application on your system.
2. Run the `bluclick.py` script.
3. Click on the game window after running the script. This action allows the script to capture the window's position and automatically click on the relevant objects.
4. Keep the game window active and avoid moving or resizing it while the script is running. The tool relies on the game window remaining in its original position and size to function correctly.


## Performance Note

Please ensure that your system has sufficient CPU resources to process the frames efficiently.



## Compatibility

This code has been tested on Linux systems. 
