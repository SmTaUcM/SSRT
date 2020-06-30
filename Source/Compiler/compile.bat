rmdir "C:\Users\smtau\Desktop\SkyShadow's Rapid Reporting Tool\Source\Compiler\dist" /S /Q
python compile.py py2exe --includes sip
mkdir "C:\Users\smtau\Desktop\SkyShadow's Rapid Reporting Tool\Source\Compiler\dist\Resource"
xcopy "C:\Users\smtau\Desktop\SkyShadow's Rapid Reporting Tool\Source\Compiler\Resource" "C:\Users\smtau\Desktop\SkyShadow's Rapid Reporting Tool\Source\Compiler\dist\Resource\" /E
rmdir "C:\Users\smtau\Desktop\SkyShadow's Rapid Reporting Tool\Source\Compiler\build" /S /Q