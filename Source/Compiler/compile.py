'''#-------------------------------------------------------------------------------------------------------------------------------------------------#
# Name:        compile.py
# Purpose:     Used to compile SSRT into SSRT.exe.
# Version:     v1.00
# Author:      Stuart. Macintosh
#
# Created:     17/01/2021
# Copyright:   Emperor's Hammer
# Licence:     None
#-------------------------------------------------------------------------------------------------------------------------------------------------#'''

#----------------------------------------------------------------------------------------------------------------------------------------------------#
#                                                                      Imports.                                                                      #
#----------------------------------------------------------------------------------------------------------------------------------------------------#
import PyInstaller.__main__
import os
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
import platform
import sys
#----------------------------------------------------------------------------------------------------------------------------------------------------#


#----------------------------------------------------------------------------------------------------------------------------------------------------#
#                                                                     Main Program.                                                                  #
#----------------------------------------------------------------------------------------------------------------------------------------------------#
# Detect the location of the SSRT folder.
os.chdir("..")
ssrtDir = os.path.abspath(os.curdir)

# Remove any old builds of SSRT.
print("\nRemoving old build files...")
shutil.rmtree(ssrtDir + "\\Compiler\\SkyShadows Rapid Reporting Tool", ignore_errors=True)

# Copy the required ttt3.ico file into the _Compiler folder.
print("\nCopying ssrt.ico icon file...")
shutil.copy(ssrtDir + "\\Resource\\icon.ico", ssrtDir + "\\Compiler\\")

# Compile SSRT.
print("\nCompiling SkyShadows Rapid Reporting Tool.exe...\n")
PyInstaller.__main__.run([
     "--onefile",
     "--windowed",
     "--icon=icon.ico",
     os.path.join(ssrtDir, "SkyShadows Rapid Reporting Tool.py"),
])
print("\SkyShadows Rapid Reporting Tool.exe created.")

# Clean up the build, copy in 'Settings' and 'Data' folders. Remove unnecessary files and renaming 'dist' to 'SSRT'.
print("\nCopying required files & Cleaning up folders...")
shutil.copy(ssrtDir + "\\config.ini", ssrtDir + "\\Compiler\\dist\\")
shutil.copy(ssrtDir + "\\srrt.ui", ssrtDir + "\\Compiler\\dist\\")
shutil.rmtree(ssrtDir + "\\Compiler\\build", ignore_errors=True)
os.remove(ssrtDir + "\\Compiler\\SkyShadows Rapid Reporting Tool.spec")
os.remove(ssrtDir + "\\Compiler\\icon.ico")
os.rename(ssrtDir + "\\Compiler\\dist", ssrtDir + "\\Compiler\\SkyShadows Rapid Reporting Tool")
#----------------------------------------------------------------------------------------------------------------------------------------------------#
