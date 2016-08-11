# Seva Alekseyev with National Institutes of Health, 2016

from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Scene.SceneNode import SceneNode
from UM.Scene.GroupDecorator import GroupDecorator
from UM.Job import Job
from math import pi, sin, cos, sqrt
import numpy

EPSILON = 0.000001 # So very crude. :(

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
    
    
DEFAULT_SUBDIV = 16 # Default subdivision factor for spheres, cones, and cylinders    

class X3DReader(MeshReader):
    def __init__(self):
        super().__init__()
        self._supported_extensions = [".x3d"]
        self._namespaces = {}
    
    # Main entry point
    # Reads the file, returns a SceneNode (possibly with nested ones), or None
    def read(self, file_name):
        try:
            self.defs = {}
            self.sceneNodes = []
            self.fileName = file_name
            
            tree = ET.parse(file_name)
            root = tree.getroot()
            
            if root.tag != "X3D":
                return None

            scale = 1000 # Default X3D unit it one meter, while Cura's is one millimeters            
            if root[0].tag == "head":
                for headNode in root[0]:
                    if headNode.tag == "unit" and headNode.attrib.get("category") == "length":
                        scale *= float(headNode.attrib["conversionFactor"])
                        break 
                scene = root[1]
            else:
                scene = root[0]
                
            if scene.tag != "Scene":
                return None 
            
            self.transform = Matrix()
            self.transform.setByScaleFactor(scale)
            
            # Traverse the scene tree, populate the sceneNodes array
            self.processChildNodes(scene)
            
            if len(self.sceneNodes) > 1:
                theScene = SceneNode()
                group_decorator = GroupDecorator()
                theScene.addDecorator(group_decorator)
                for node in self.sceneNodes:
                    theScene.addChild(node)
                theScene.setSelectable(True)
            elif len(self.sceneNodes) == 1:
                theScene = self.sceneNodes[0]
            else: # No shapes read :(
                return None
            theScene.setName(file_name)
        except Exception as e:
            Logger.log("e", "exception occured in x3d reader: %s", e)

        try:
            boundingBox = theScene.getBoundingBox()
            boundingBox.isValid()
        except:
            return None

        return theScene
    
    # ------------------------- XML tree traversal
  
    def processNode(self, xmlNode):
        xmlNode =  self.resolveDefUse(xmlNode)
        if xmlNode is None:
            return
        
        tag = xmlNode.tag
        if tag in ("Group", "StaticGroup", "CADAssembly", "CADFace", "CADLayer", "CADPart", "Collision"):
            self.processChildNodes(xmlNode)
        elif tag == "LOD":
            self.processNode(xmlNode[0])
        elif tag == "Transform":
            self.processTransform(xmlNode)
        elif tag == "Shape":
            self.processShape(xmlNode)
            
            
    def processShape(self, xmlNode):
        # Find the geometry and the appearance inside the Shape
        geometry = appearance = None
        for subNode in xmlNode:
            if subNode.tag == "Appearance" and not appearance:
                appearance = self.resolveDefUse(subNode)
            elif subNode.tag in self.geometryImporters and not geometry:
                geometry = self.resolveDefUse(subNode)
        
        # TODO: appearance is completely ignored. At least apply the material color...        
        if not geometry is None:
            try:
                bui = MeshBuilder()
                self.geometryImporters[geometry.tag](self, geometry, bui)
                
                bui.calculateNormals()
                bui.setFileName(self.fileName)
                
                sceneNode = SceneNode()
                if "DEF" in geometry.attrib:
                    sceneNode.setName(geometry.tag + "#" + geometry.attrib["DEF"])
                else:
                    sceneNode.setName(geometry.tag)
                     
                sceneNode.setMeshData(bui.build().getTransformed(self.transform))
                sceneNode.setSelectable(True)
                self.sceneNodes.append(sceneNode)
                
            except Exception as e:
                Logger.log("e", "exception occured in x3d reader while reading %s: %s", geometry.tag, e)
        
    # Returns the referenced node if the node has USE, the same node otherwise.
    # May return None is USE points at a nonexistent node
    # In X3DOM, when both DEF and USE are in the same node, DEF is ignored.
    # Big caveat: XML element objects may evaluate to boolean False!!!
    # Don't ever use "if node:", use "if not node is None:" instead
    def resolveDefUse(self, node):
        USE = node.attrib.get("USE")
        if USE:
            return self.defs.get(USE, None)

        DEF = node.attrib.get("DEF")            
        if DEF:
            self.defs[DEF] = node 
        return node
    
    def processChildNodes(self, node):
        for c in node:
            self.processNode(c)
            Job.yieldThread()
    
    # Since this is a grouping node, will recurse down the tree.
    # According to the spec, the final transform matrix is:
    # T * C * R * SR * S * -SR * -C
    # Where SR corresponds to the rotation matrix to scaleOrientation
    # C and SR are rather exotic. S, slightly less so. 
    def processTransform(self, node):
        rot = readRotation(node, "rotation", (0, 0, 1, 0)) # (angle, axisVactor) tuple
        trans = readVector(node, "translation", (0, 0, 0)) # Vector
        scale = readVector(node, "scale", (1, 1, 1)) # Vector
        center = readVector(node, "center", (0, 0, 0)) # Vector
        scaleOrient = readRotation(node, "scaleOrientation", (0, 0, 1, 0)) # (angle, axisVactor) tuple
        
        # Store the previous transform; in Cura, the default matrix multiplication is in place        
        prev = Matrix(self.transform.getData()) # It's deep copy, I've checked
        
        # The rest of transform manipulation will be applied in place
        gotCenter = (center.x != 0 or center.y != 0 or center.z != 0)
        
        T = self.transform
        if trans.x != 0 or trans.y != 0 or trans.z !=0:
            T.translate(trans)
        if gotCenter:
            T.translate(center)
        if rot[0] != 0:
            T.rotateByAxis(*rot)
        if scale.x != 1 or scale.y != 1 or scale.z != 1:
            gotScaleOrient = scaleOrient[0] != 0
            if gotScaleOrient:
                T.rotateByAxis(*scaleOrient)
            # No scale by vector in place operation in UM
            S = Matrix()
            S.setByScaleVector(scale)
            T.multiply(S)
            if gotScaleOrient:
                T.rotateByAxis(-scaleOrient[0], scaleOrient[1])
        if gotCenter:
            T.translate(-center)
            
        self.processChildNodes(node)
        self.transform = prev
    
    # ------------------------- Geometry importers
    # They are supposed to fill the MeshBuilder object with vertices and faces, the caller will do the rest
    
    # Primitives

    def geomBox(self, node, bui):
        size = readFloatArray(node, "size", [2, 2, 2])
        bui.addCube(size[0], size[1], size[2])
    
    # The sphere is subdivided into nr rings and ns segments
    def geomSphere(self, node, bui):
        r = readFloat(node, "radius", 0.5)
        subdiv = readIntArray(node, 'subdivision', None)
        if subdiv:
            if len(subdiv) == 1:
                nr = ns = subdiv[0]
            else:
                (nr, ns) = subdiv
        else:
            nr = ns = DEFAULT_SUBDIV
            
        lau = pi / nr  # Unit angle of latitude (rings) for the given tesselation
        lou = 2 * pi / ns  # Unit angle of longitude (segments)
        
        bui.reserveFaceAndVertexCount(ns*(nr*2 - 2), 2 + (nr + 1)*ns)
        
        # +y and -y poles
        bui.addVertex(0, r, 0)
        bui.addVertex(0, -r, 0)
        
        # The non-polar vertices go from x=0, negative z plane counterclockwise -
        # to -x, to +z, to +x, back to -z
        for ring in range(1, nr):
            for seg in range(ns):
                bui.addVertex(-r*sin(lou * seg) * sin(lau * ring),
                          r*cos(lau * ring),
                          -r*cos(lou * seg) * sin(lau * ring))
                
        vb = 2 + (nr - 2) * ns  # First vertex index for the bottom cap
    
        # Faces go in order: top cap, sides, bottom cap.
        # Sides go by ring then by segment.
    
        # Caps
        # Top cap face vertices go in order: down right up
        # (starting from +y pole)
        # Bottom cap goes: up left down (starting from -y pole)
        for seg in range(ns):
            addTri(bui, 0, seg + 2, (seg + 1) % ns + 2)
            addTri(bui, 1, vb + (seg + 1) % ns, vb + seg)
    
        # Sides
        # Side face vertices go in order:  down right upleft, downright up left
        for ring in range(nr - 2):
            tvb = 2 + ring * ns
            # First vertex index for the top edge of the ring
            bvb = tvb + ns
            # First vertex index for the bottom edge of the ring
            for seg in range(ns):
                nseg = (seg + 1) % ns
                addQuad(bui, tvb + seg, bvb + seg, bvb + nseg, tvb + nseg)
        
    def geomCone(self, node, bui):
        r = readFloat(node, "bottomRadius", 1)
        height = readFloat(node, "height", 2)
        bottom = readBoolean(node, "bottom", True)
        side = readBoolean(node, "side", True)
        n = readInt(node, 'subdivision', DEFAULT_SUBDIV)
        
        d = height / 2
        angle = 2 * pi / n
    
        bui.reserveFaceAndVertexCount((n if side else 0) + (n-1 if bottom else 0), n+1)
    
        bui.addVertex(0, d, 0)
        for i in range(n):
            bui.addVertex(-r * sin(angle * i), -d, -r * cos(angle * i))
                    
        # Side face vertices go: up down right
        if side:
            for i in range(n):
                addTri(bui, 1 + (i + 1) % n, 0, 1 + i)
        if bottom:
            for i in range(2, n):
                addTri(bui, 1, i, i+1)
    
    def geomCylinder(self, node, bui):
        r = readFloat(node, "radius", 1)
        height = readFloat(node, "height", 2)
        bottom = readBoolean(node, "bottom", True)
        side = readBoolean(node, "side", True)
        top = readBoolean(node, "top", True)
        n = readInt(node, "subdivision", DEFAULT_SUBDIV)
        
        nn = n * 2
        angle = 2 * pi / n
        hh = height/2
        
        bui.reserveFaceAndVertexCount((nn if side else 0) + (n - 2 if top else 0) + (n - 2 if bottom else 0), nn)
        
        # The seam is at x=0, z=-r, vertices go ccw -
        # to pos x, to neg z, to neg x, back to neg z
        for i in range(n):
            rs = -r * sin(angle * i)
            rc = -r * cos(angle * i)
            bui.addVertex(rs, hh, rc)
            bui.addVertex(rs, -hh, rc)
        
        if side:
            for i in range(n):
                ni = (i + 1) % n
                addQuad(bui, ni * 2 + 1, ni * 2, i * 2, i * 2 + 1)
            
        for i in range(2, nn-3, 2):
            if top:
                addTri(bui, 0, i, i+2)
            if bottom:
                addTri(bui, 1, i+1, i+3)
    
# Semi-primitives

    def geomElevationGrid(self, node, bui):
        dx = readFloat(node, "xSpacing", 1)
        dz = readFloat(node, "zSpacing", 1)
        nx = readInt(node, "xDimension", 0)
        nz = readInt(node, "zDimension", 0)
        height = readFloatArray(node, "height", False)
        ccw = readBoolean(node, "ccw", True)
        
        if nx <= 0 or nz <= 0 or len(height) < nx*nz:
            return # That's weird, the wording of the standard suggests grids with zero quads are somehow valid
        
        bui.reserveFaceAndVertexCount(2*(nx-1)*(nz-1), nx*nz)
        
        for z in range(nz):
            for x in range(nx):
                bui.addVertex(x * dx, height[z*nx + x], z * dz)
                
        for z in range(1, nz):
            for x in range(1, nx):
                addTriFlip(bui, (z - 1)*nx + x - 1, z*nx + x, (z - 1)*nx + x, ccw)
                addTriFlip(bui, (z - 1)*nx + x - 1, z*nx + x - 1, z*nx + x, ccw)
    
    def geomExtrusion(self, node, bui):
        ccw = readBoolean(node, "ccw", True)
        beginCap = readBoolean(node, "beginCap", True)
        endCap = readBoolean(node, "endCap", True)
        cross = readFloatArray(node, "crossSection", (1, 1, 1, -1, -1, -1, -1, 1, 1, 1))
        cross = [(cross[i], cross[i+1]) for i in range(0, len(cross), 2)]
        spine = readFloatArray(node, "spine", (0, 0, 0, 0, 1, 0))
        spine = [(spine[i], spine[i+1], spine[i+2]) for i in range(0, len(spine), 3)]
        orient = readFloatArray(node, 'orientation', None)
        if orient:
            orient = [toNumpyRotation(orient[i:i+4]) if orient[i+3] != 0 else None for i in range(0, len(orient), 4)]
        scale = readFloatArray(node, "scale", None)
        if scale:
            scale = [numpy.array(((scale[i], 0, 0), (0, 1, 0), (0, 0, scale[i+1])))
                     if scale[i] != 1 or scale[i+1] != 1 else None for i in range(0, len(scale), 2)]
        
        
        # Special treatment for the closed spine and cross section.
        # Let's save some memory by not creating identical but distinct vertices;
        # later we'll introduce conditional logic to link the last vertex with
        # the first one where necessary.
        crossClosed = cross[0] == cross[-1]
        if crossClosed:
            cross = cross[:-1]
        nc = len(cross)
        cross = [numpy.array((c[0], 0, c[1])) for c in cross]
        ncf = nc if crossClosed else nc - 1
        # Face count along the cross; for closed cross, it's the same as the
        # respective vertex count
    
        spineClosed = spine[0] == spine[-1]
        if spineClosed:
            spine = spine[:-1]
        ns = len(spine)
        spine = [Vector(*s) for s in spine]
        nsf = ns if spineClosed else ns - 1
    
        # This will be used for fallback, where the current spine point joins
        # two collinear spine segments. No need to recheck the case of the
        # closed spine/last-to-first point juncture; if there's an angle there,
        # it would kick in on the first iteration of the main loop by spine.
        def findFirstAngleNormal():
            for i in range(1, ns - 1):
                spt = spine[i]
                z = (spine[i + 1] - spt).cross(spine[i - 1] - spt)
                if z.length() > EPSILON:
                    return z
            # All the spines are collinear. Fallback to the rotated source
            # XZ plane.
            # TODO: handle the situation where the first two spine points match
            v = spine[1] - spine[0]
            orig_y = Vector(0, 1, 0)
            orig_z = Vector(0, 0, 1)
            if v.cross(orig_y).length() > EPSILON:
                # Spine at angle with global y - rotate the z accordingly
                a = v.cross(orig_y) # Axis of rotation to get to the Z
                (x, y, z) = a.normalized().getData()  
                s = a.length()/v.length()
                c = sqrt(1-s*s)
                t = 1-c
                m = numpy.array((
                    (x * x * t + c,  x * y * t + z*s, x * z * t - y * s),
                    (x * y * t - z*s, y * y * t + c, y * z * t + x * s),
                    (x * z * t + y * s, y * z * t - x * s, z * z * t + c)))
                orig_z = Vector(*m.dot(orig_z.getData()))
            return orig_z
    
        bui.reserveFaceAndVertexCount(2*nsf*ncf + (nc - 2 if beginCap else 0) + (nc - 2 if endCap else 0), ns*nc)

        z = None
        for i, spt in enumerate(spine):
            if (i > 0 and i < ns - 1) or spineClosed:
                snext = spine[(i + 1) % ns]
                sprev = spine[(i - 1 + ns) % ns]
                y = snext - sprev
                vnext = snext - spt
                vprev = sprev - spt
                try_z = vnext.cross(vprev)
                # Might be zero, then all kinds of fallback
                if try_z.length() > EPSILON:
                    if z is not None and try_z.dot(z) < 0:
                        try_z = -try_z
                    z = try_z
                elif not z:  # No z, and no previous z.
                    # Look ahead, see if there's at least one point where
                    # spines are not collinear.
                    z = findFirstAngleNormal()
            elif i == 0:  # And non-crossed
                snext = spine[i + 1]
                y = snext - spt
                z = findFirstAngleNormal()
            else:  # last point and not crossed
                sprev = spine[i - 1]
                y = spt - sprev
                # If there's more than one point in the spine, z is already set.
                # One point in the spline is an error anyway.
    
            z = z.normalized()
            y = y.normalized()
            x = y.cross(z) # Already normalized
            m = numpy.array(((x.x, y.x, z.x), (x.y, y.y, z.y), (x.z, y.z, z.z)))
            
            # Columns are the unit vectors for the xz plane for the cross-section
            if orient:
                mrot = orient[i] if len(orient) > 1 else orient[0]
                if not mrot is None:
                    m = m.dot(mrot)  # Tested against X3DOM, the result matches, still not sure :(
                    
            if scale:
                mscale = scale[i] if len(scale) > 1 else scale[0]
                if not mscale is None:
                    m = m.dot(mscale)
                    
            # First the cross-section 2-vector is scaled,
            # then rotated (which may make it a 3-vector),
            # then applied to the xz plane unit vectors
                    
            sptv3 = numpy.array(spt.getData()[:3])
            for cpt in cross:
                v = sptv3 + m.dot(cpt)
                bui.addVertex(*v)
    
        if beginCap:
            addFace(bui, [x for x in range(nc - 1, -1, -1)], ccw)
    
        # Order of edges in the face: forward along cross, forward along spine,
        # backward along cross, backward along spine, flipped if now ccw.
        # This order is assumed later in the texture coordinate assignment;
        # please don't change without syncing.
    
        for s in range(ns - 1):
            for c in range(ncf):
                addQuadFlip(bui, s * nc + c, s * nc + (c + 1) % nc,
                    (s + 1) * nc + (c + 1) % nc, (s + 1) * nc + c, ccw)
    
        if spineClosed:
            # The faces between the last and the first spine points
            b = (ns - 1) * nc
            for c in range(ncf):
                addQuadFlip(bui, b + c, b + (c + 1) % nc,
                    (c + 1) % nc, c, ccw)
                        
        if endCap:
            addFace(bui, [(ns - 1) * nc + x for x in range(0, nc)], ccw)
    
# Triangle meshes

    # Helper for numerous nodes with a Coordinate subnode holding vertices
    # That all triangle meshes and IndexedFaceSet
    # nFaces can be a function, in case the face count is a function of coord 
    def startCoordMesh(self, node, bui, nFaces):
        ccw = readBoolean(node, "ccw", True)
        coord = self.readVertices(node)
        if hasattr(nFaces, '__call__'):
            nFaces = nFaces(coord)
        bui.reserveFaceAndVertexCount(nFaces, len(coord))
        for pt in coord:
            bui.addVertex(*pt)
            
        return ccw
        

    def geomIndexedTriangleSet(self, node, bui):
        index = readIntArray(node, "index", [])
        nFaces = len(index) // 3
        ccw = self.startCoordMesh(node, bui, nFaces)
        
        for i in range(0, nFaces*3, 3):
            addTriFlip(bui, index[i], index[i+1], index[i+2], ccw)
    
    def geomIndexedTriangleStripSet(self, node, bui):
        strips = readIndex(node, "index")
        ccw = self.startCoordMesh(node, bui, sum([len(strip) - 2 for strip in strips]))
            
        for strip in strips:
            sccw = ccw # Running CCW value, reset for each strip
            for i in range(len(strip) - 2):
                addTriFlip(bui, strip[i], strip[i+1], strip[i+2], sccw)
                sccw = not sccw
    
    def geomIndexedTriangleFanSet(self, node, bui):
        fans = readIndex(node, "index")
        ccw = self.startCoordMesh(node, bui, sum([len(fan) - 2 for fan in fans]))
        
        for fan in fans:
            for i in range(1, len(fan) - 1):
                addTriFlip(bui, fan[0], fan[i], fan[i+1], ccw)
   
    def geomTriangleSet(self, node, bui):
        ccw = self.startCoordMesh(node, bui, lambda coord: len(coord) // 3)
        for i in range(0, len(bui.getVertices()), 3):
            addTriFlip(bui, i, i+1, i+2, ccw)
    
    def geomTriangleStripSet(self, node, bui):
        strips = readIntArray(node, "stripCount", [])
        ccw = self.startCoordMesh(node, bui, sum([n-2 for n in strips]))
            
        vb = 0
        for n in strips:
            sccw = ccw
            for i in range(n-2): 
                addTriFlip(bui, vb+i, vb+i+1, vb+i+2, sccw)
                sccw = not sccw
            vb += n
    
    def geomTriangleFanSet(self, node, bui):
        fans = readIntArray(node, "fanCount", [])
        ccw = self.startCoordMesh(node, bui, sum([n-2 for n in fans]))
        
        vb = 0
        for n in fans:
            for i in range(1, n-1): 
                addTriFlip(bui, vb, vb+i, vb+i+1, ccw)
            vb += n
            
    # Quad geometries from the CAD module, might be relevant for printing
    
    def geomQuadSet(self, node, bui):
        ccw = self.startCoordMesh(node, bui, lambda coord: 2*(len(coord) // 4))
        for i in range(0, len(bui.getVertices()), 4):
            addQuadFlip(bui, i, i+1, i+2, i+3, ccw)
            
    def geomIndexedQuadSet(self, node, bui):
        index = readIntArray(node, "index", [])
        nQuads = len(index) // 4
        ccw = self.startCoordMesh(node, bui, nQuads*2)
        
        for i in range(0, nQuads*4, 4):
            addQuadFlip(bui, index[i], index[i+1], index[i+2], index[i+3], ccw)
    
    # General purpose polygon mesh

    def geomIndexedFaceSet(self, node, bui):
        faces = readIndex(node, "coordIndex")
        ccw = self.startCoordMesh(node, bui, sum([len(face) - 2 for face in faces]))
            
        for face in faces:
            if len(face) == 3:
                addTriFlip(bui, face[0], face[1], face[2], ccw)
            elif len(face) > 3:
                addFace(bui, face, ccw)
                
    geometryImporters = {
        'IndexedFaceSet': geomIndexedFaceSet,
        'IndexedTriangleSet': geomIndexedTriangleSet,
        'IndexedTriangleStripSet': geomIndexedTriangleStripSet,
        'IndexedTriangleFanSet': geomIndexedTriangleFanSet,
        'TriangleSet': geomTriangleSet,
        'TriangleStripSet': geomTriangleStripSet,
        'TriangleFanSet': geomTriangleFanSet,
        'QuadSet': geomQuadSet,
        'IndexedQuadSet': geomIndexedQuadSet,
        'ElevationGrid': geomElevationGrid,
        'Extrusion': geomExtrusion,
        'Sphere': geomSphere,
        'Box': geomBox,
        'Cylinder': geomCylinder,
        'Cone': geomCone
    }
    
    # Parses the Coordinate.@point field
    def readVertices(self, node):
        for c in node:
            if c.tag == "Coordinate":
                c = self.resolveDefUse(c)
                if not c is None:
                    pt = c.attrib.get("point")
                    if pt:
                        co = [float(x) for x in pt.split()]
                        # Group by three
                        return [(co[i], co[i+1], co[i+2]) for i in range(0, (len(co) // 3)*3, 3)]
        return []
    
# ------------------------------------------------------------
# X3D field parsers
# ------------------------------------------------------------
def readFloatArray(node, attr, default):
    s = node.attrib.get(attr)
    if not s:
        return default
    return [float(x) for x in s.split()]

def readIntArray(node, attr, default):
    s = node.attrib.get(attr)
    if not s:
        return default
    return [int(x, 0) for x in s.split()]

def readFloat(node, attr, default):
    s = node.attrib.get(attr)
    if not s:
        return default
    return float(s)

def readInt(node, attr, default):
    s = node.attrib.get(attr)
    if not s:
        return default
    return int(s, 0)
     
def readBoolean(node, attr, default):
    s = node.attrib.get(attr)
    if not s:
        return default
    return s.lower() == "true"

def readVector(node, attr, default):
    v = readFloatArray(node, attr, default)
    return Vector(v[0], v[1], v[2])

def readRotation(node, attr, default):
    v = readFloatArray(node, attr, default)
    return (v[3], Vector(v[0], v[1], v[2]))

# Returns the -1-separated runs
def readIndex(node, attr):
    v = readIntArray(node, attr, [])
    chunks = []
    chunk = []
    for i in range(len(v)):
        if v[i] == -1:
            if chunk:
                chunks.append(chunk)
                chunk = []
        else:
            chunk.append(v[i])
    if chunk:
        chunks.append(chunk)
    return chunks  
    
# Mesh builder helpers

def addTri(bui, a, b, c):
    bui._indices[bui._face_count, 0] = a
    bui._indices[bui._face_count, 1] = b
    bui._indices[bui._face_count, 2] = c
    bui._face_count += 1
    
def addTriFlip(bui, a, b, c, ccw):
    if ccw:
        addTri(bui, a, b, c)
    else:
        addTri(bui, b, a, c)
    
# Needs to be convex, but not necessaily planar
# Assumed ccw, cut along the ac diagonal
def addQuad(bui, a, b, c, d):
    addTri(bui, a, b, c)
    addTri(bui, c, d, a)
    
def addQuadFlip(bui, a, b, c, d, ccw):
    if ccw:
        addTri(bui, a, b, c)
        addTri(bui, c, d, a)
    else:
        addTri(bui, a, c, b)
        addTri(bui, c, a, d)
    
    
# Arbitrary polygon triangulation.
# Doesn't assume convexity and doesn't check the "convex" flag in the file.
# Works by the "cutting of ears" algorithm:
# - Find an outer vertex with the smallest angle and no vertices inside its adjacent triangle
# - Remove the triangle at that vertex
# - Repeat until done
# Vertex coordinates are supposed to be already in the mesh builder object
def addFace(bui, indices, ccw):
    # Resolve indices to coordinates for faster math
    n = len(indices)
    verts = bui.getVertices()
    face = [Vector(verts[i, 0], verts[i, 1], verts[i, 2]) for i in indices]
    
    # Need a normal to the plane so that we can know which vertices form inner angles
    normal = findOuterNormal(face)
        
    if not normal: # Couldn't find an outer edge, non-planar polygon maybe?
        return
    
    # Find the vertex with the smallest inner angle and no points inside, cut off. Repeat until done
    m = len(face)
    vi = [i for i in range(m)] # We'll be using this to kick vertices from the face
    while m > 3:
        maxCos = EPSILON # We don't want to check anything on Pi angles
        iMin = 0 # max cos corresponds to min angle
        for i in range(m):
            inext = (i + 1) % m
            iprev = (i + m - 1) % m
            v = face[vi[i]]
            next = face[vi[inext]] - v
            prev = face[vi[iprev]] - v
            nextXprev = next.cross(prev)
            if nextXprev.dot(normal) > EPSILON: # If it's an inner angle
                cos = next.dot(prev) / (next.length() * prev.length())
                if cos > maxCos:
                    # Check if there are vertices inside the triangle
                    noPointsInside = True
                    for j in range(m):
                        if j != i and j != iprev and j != inext:
                            vx = face[vi[j]] - v
                            if pointInsideTriangle(vx, next, prev, nextXprev):
                                noPointsInside = False
                                break
                            
                    if noPointsInside:
                        maxCos = cos
                        iMin = i
                        
        addTriFlip(bui, indices[vi[(iMin + m - 1) % m]], indices[vi[iMin]], indices[vi[(iMin + 1) % m]], ccw)
        vi.pop(iMin)
        m -= 1
    addTriFlip(bui, indices[vi[0]], indices[vi[1]], indices[vi[2]], ccw)
  
  
# Given a face as a sequence of vectors, returns a normal to the polygon place that forms a right triple
# with a vector along the polygon sequence and a vector backwards
def findOuterNormal(face):
    n = len(face)
    for i in range(n):
        for j in range(i+1, n):
            edge = face[j] - face[i]
            if edge.length() > EPSILON:
                edge = edge.normalized()
                prevRejection = Vector()
                isOuter = True
                for k in range(n):
                    if k != i and k != j:
                        pt = face[k] - face[i]
                        pte = pt.dot(edge)
                        rejection = pt - edge*pte
                        if rejection.dot(prevRejection) < -EPSILON: # points on both sides of the edge - not an outer one
                            isOuter = False
                            break
                        elif rejection.length() > prevRejection.length(): # Pick a greater rejection for numeric stability 
                            prevRejection = rejection
                        
                if isOuter: # Found an outer edge, prevRejection is the rejection inside the face. Generate a normal.
                    return edge.cross(prevRejection)

    return False
    
# Assumes the vectors are either parallel or antiparallel and the denominator is nonzero.
# No error handling.
# For stability, taking the ration between the biggest coordinates would be better; none of that, either.   
def ratio(a, b):
    if b.x > EPSILON:
        return a.x / b.x
    elif b.y > EPSILON:
        return a.y / b.y
    else:
        return a.z / b.z    
    
def pointInsideTriangle(vx, next, prev, nextXprev):
    vxXprev = vx.cross(prev)
    r = ratio(vxXprev, nextXprev)
    if r < 0:
        return False;
    vxXnext = vx.cross(next);
    s = -ratio(vxXnext, nextXprev)
    return s > 0 and (s + r) < 1
    
def toNumpyRotation(rot):
    (x, y, z) = rot[:3]
    a = rot[3]  
    s = sin(a)
    c = cos(a)
    t = 1-c
    return numpy.array((
        (x * x * t + c,  x * y * t - z*s, x * z * t + y * s),
        (x * y * t + z*s, y * y * t + c, y * z * t - x * s),
        (x * z * t - y * s, y * z * t + x * s, z * z * t + c)))    

    
    