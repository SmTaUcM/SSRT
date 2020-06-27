# USAGE: from cmd.exe type 'python compile.py py2exe --includes sip'

# Copy Resource folder into dist folder.

from distutils.core import setup
import py2exe

setup(console=["C:\Users\smtau\Desktop\SkyShadow's Rapid Reporting Tool\Source\SRRT.py"])
