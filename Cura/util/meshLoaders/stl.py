from __future__ import absolute_import

import sys
import os
import struct
import time

from Cura.util import mesh

def _loadAscii(m, f):
	cnt = 0
	for lines in f:
		for line in lines.split('\r'):
			if 'vertex' in line:
				cnt += 1
	m._prepareFaceCount(int(cnt) / 3)
	f.seek(5, os.SEEK_SET)
	cnt = 0
	data = [None,None,None]
	for lines in f:
		for line in lines.split('\r'):
			if 'vertex' in line:
				data[cnt] = line.split()[1:]
				cnt += 1
				if cnt == 3:
					m._addFace(float(data[0][0]), float(data[0][1]), float(data[0][2]), float(data[1][0]), float(data[1][1]), float(data[1][2]), float(data[2][0]), float(data[2][1]), float(data[2][2]))
					cnt = 0

def _loadBinary(m, f):
	#Skip the header
	f.read(80-5)
	faceCount = struct.unpack('<I', f.read(4))[0]
	m._prepareFaceCount(faceCount)
	for idx in xrange(0, faceCount):
		data = struct.unpack("<ffffffffffffH", f.read(50))
		m._addFace(data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11])

def loadSTLscene(filename):
	obj = mesh.printableObject()
	m = obj._addMesh()

	f = open(filename, "rb")
	if f.read(5).lower() == "solid":
		_loadAscii(m, f)
		if m.vertexCount < 3:
			f.seek(5, os.SEEK_SET)
			_loadBinary(m, f)
	else:
		_loadBinary(m, f)
	f.close()
	obj._postProcessAfterLoad()
	return [obj]

def saveAsSTL(mesh, filename):
	f = open(filename, 'wb')
	#Write the STL binary header. This can contain any info, except for "SOLID" at the start.
	f.write(("CURA BINARY STL EXPORT. " + time.strftime('%a %d %b %Y %H:%M:%S')).ljust(80, '\000'))
	#Next follow 4 binary bytes containing the amount of faces, and then the face information.
	f.write(struct.pack("<I", int(mesh.vertexCount / 3)))
	for idx in xrange(0, mesh.vertexCount, 3):
		v1 = mesh.vertexes[idx]
		v2 = mesh.vertexes[idx+1]
		v3 = mesh.vertexes[idx+2]
		f.write(struct.pack("<fff", 0.0, 0.0, 0.0))
		f.write(struct.pack("<fff", v1[0], v1[1], v1[2]))
		f.write(struct.pack("<fff", v2[0], v2[1], v2[2]))
		f.write(struct.pack("<fff", v3[0], v3[1], v3[2]))
		f.write(struct.pack("<H", 0))
	f.close()

if __name__ == '__main__':
	for filename in sys.argv[1:]:
		m = stlModel().load(filename)
		print("Loaded %d faces" % (m.vertexCount / 3))
		parts = m.splitToParts()
		for p in parts:
			saveAsSTL(p, "export_%i.stl" % parts.index(p))

