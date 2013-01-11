from __future__ import absolute_import

from Cura.util import mesh

class objModel(mesh.mesh):
	def __init__(self):
		super(objModel, self).__init__()

	def load(self, filename):
		vertexList = []
		faceList = []
		
		f = open(filename, "r")
		for line in f:
			parts = line.split()
			if len(parts) < 1:
				continue
			if parts[0] == 'v':
				vertexList.append([float(parts[1]), float(parts[2]), float(parts[3])])
			if parts[0] == 'f':
				parts = map(lambda p: p.split('/')[0], parts)
				for idx in xrange(1, len(parts)-2):
					faceList.append([int(parts[1]), int(parts[idx+1]), int(parts[idx+2])])
		f.close()
		
		self._prepareVertexCount(len(faceList) * 3)
		for f in faceList:
			i = f[0] - 1
			self.addVertex(vertexList[i][0], vertexList[i][1], vertexList[i][2])
			i = f[1] - 1
			self.addVertex(vertexList[i][0], vertexList[i][1], vertexList[i][2])
			i = f[2] - 1
			self.addVertex(vertexList[i][0], vertexList[i][1], vertexList[i][2])
		
		self._postProcessAfterLoad()
		return self
	
