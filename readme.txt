This applet explainins the concept of laser cooling. It is essentially a clone of a
similar applet that was developed in JILA at the University of Colorado, as a part of the
Physics-2000 website. Unfortunately, this applet was written in Java and is no longer available.
Because this applet is incredibly instructive in courses on ultracold gases, I made this
clone in today's most popular programming language: Python. 

The applet is written using the Pygame and NumPy packages. Only these two libraries and the
Python Standard Library are required for running the code. The Python code can be packaged into
a Windows executable using PyInstaller on the provided LaserCooling_addfiles.spec file.
The executable can then be run on a machine that does not have Python, Pygame, or NumPy installed. 
To make the executable, open a command prompt, go to the directory with this file, and run the
following commands:

pip install pygame
pip install numpy
pip install PyInstaller
pyinstaller LaserCooling_addfiles.spec

The resulting executable can be found in the dist/ folder.

Feel free to modify or distribute this applet at will, as long as you do not remove the credits
below.

Current implementation: Matthew Houtput, University of Antwerp, 2022-10-25
Original idea and implementation: Physics-2000, JILA, University of Colorado, Boulder

