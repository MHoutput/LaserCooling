This applet explainins the concept of laser cooling. It is essentially a clone of a
similar applet that was developed in JILA at the University of Colorado, as a part of the
Physics-2000 website. Unfortunately, this applet was written in Java and is no longer available.
Because this applet is incredibly instructive in courses on ultracold gases, I made this
clone in today's most popular programming language: Python. 

The applet is written using the Pygame and NumPy packages. Only these two libraries and the
Python Standard Library are required for running the code. Pygame and NumPy can be installed
by running:

pip install pygame
pip install numpy

The Python code can be packaged into a Windows executable using PyInstaller, that can be run
without installing Python, Pygame, or NumPy. This can be done by running PyInstaller in this folder
using the provided .spec file:

pip install PyInstaller
pyinstaller Evaporation_addfiles.spec

Feel free to modify or distribute this applet at will, as long as you do not remove the credits
below.

Current implementation: Matthew Houtput, University of Antwerp, 2022-10-25
Original idea and implementation: Physics-2000, JILA, University of Colorado, Boulder

