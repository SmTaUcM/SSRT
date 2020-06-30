# USAGE: from cmd.exe type 'python compile.py py2exe --includes sip'

# NOTE: C:\Python27\Lib\site-packages\PyQt4\uic\port_v3 must be deleted to allow Py2EXE to work.

# Copy Resource folder into dist folder.

from distutils.core import setup
import py2exe

setup(windows=["C:\Users\smtau\Desktop\SkyShadow's Rapid Reporting Tool\Source\SRRT.py"])
