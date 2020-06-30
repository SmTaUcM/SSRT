rmdir "C:\Users\smtau\Desktop\SkyShadow's Rapid Reporting Tool\Source\Compiler\dist" /S /Q
python compile.py py2exe --includes sip
copy "C:\Users\smtau\Desktop\SkyShadow's Rapid Reporting Tool\Source\Resource\srrt.ui" "C:\Users\smtau\Desktop\SkyShadow's Rapid Reporting Tool\Source\Compiler\dist\" 
rmdir "C:\Users\smtau\Desktop\SkyShadow's Rapid Reporting Tool\Source\Compiler\build" /S /Q