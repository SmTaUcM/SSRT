rmdir "D:\Stuart\Downloads\TIECorps\Tools\SkyShadow's Rapid Reporting Tool\Source\Compiler\dist" /S /Q
python compile.py py2exe --includes sip
copy "D:\Stuart\Downloads\TIECorps\Tools\SkyShadow's Rapid Reporting Tool\Source\Resource\srrt.ui" "D:\Stuart\Downloads\TIECorps\Tools\SkyShadow's Rapid Reporting Tool\Source\Compiler\dist\" 
rmdir "D:\Stuart\Downloads\TIECorps\Tools\SkyShadow's Rapid Reporting Tool\Source\Compiler\build" /S /Q