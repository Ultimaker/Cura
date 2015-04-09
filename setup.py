from distutils.core import setup
import py2exe
import UM
import UM.Qt
import os
import re
import shutil
import site

includes = ['sip', 'ctypes', 'UM', 'PyQt5.QtNetwork', 'PyQt5._QOpenGLFunctions_2_0', 'serial', 'Arcus', 'google', 'google.protobuf', 'google.protobuf.descriptor', 'xml.etree', 'xml.etree.ElementTree']
# Include all the UM modules in the includes. As py2exe fails to properly find all the dependencies due to the plugin architecture.
for dirpath, dirnames, filenames in os.walk('../UM'):
	if '__' in dirpath:
		continue
	dirpath = dirpath.split(os.path.sep)
	dirpath[0] = 'UM'
	module_name = '.'.join(dirpath)
	if os.path.isfile('../' + os.path.sep.join(dirpath) + '/__init__.py'):
		includes += [module_name]
		for filename in filenames:
			if '__' in filename or not filename.endswith('.py'):
				continue
			includes += [module_name + '.' + os.path.splitext(filename)[0]]


print('Removing previous distribution package')
shutil.rmtree('dist', True)

setup(name="Cura",
		version="2.0",
		author="Ultimaker",
		author_email="d.braam@ultimaker.com",
		url="http://software.ultimaker.com/",
		license="GNU AFFERO GENERAL PUBLIC LICENSE (AGPL)",
		scripts=["printer.py", "PrinterApplication.py"],
		#windows=[{"script": "printer.py", "dest_name": "Cura"}],
		console=[{"script": "printer.py"}],
		options={"py2exe": {"skip_archive": False, "includes": includes}})

print('Coping Cura plugins.')
shutil.copytree('../plugins', 'dist/plugins')
print('Coping Cura qml.')
shutil.copytree('qml', 'dist/qml')
print('Coping resources.')
shutil.copytree('../resources', 'dist/resources')
print('Coping resources.')
shutil.copytree('../UM/Qt/qml/UM', 'dist/qml/UM')
for site_package in site.getsitepackages():
	qt_origin_path = os.path.join(site_package, 'PyQt5')
	if os.path.isdir(qt_origin_path):
		print('Coping PyQt5 plugins from: %s' % qt_origin_path)
		shutil.copytree(os.path.join(qt_origin_path, 'plugins'), 'dist/PyQt5/plugins')
		print('Coping PyQt5 QtQuick from: %s' % qt_origin_path)
		shutil.copytree(os.path.join(qt_origin_path, 'qml/QtQuick'), 'dist/qml/QtQuick')
		shutil.copytree(os.path.join(qt_origin_path, 'qml/QtQuick.2'), 'dist/qml/QtQuick.2')
		print('Coping PyQt5 svg library from: %s' % qt_origin_path)
		shutil.copy(os.path.join(qt_origin_path, 'Qt5Svg.dll'), 'dist/Qt5Svg.dll')
os.rename('dist/printer.exe', 'dist/Cura.exe')
