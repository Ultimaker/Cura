import itertools
import logging
import os
from os.path import dirname, join, basename
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib

import infiniteworld
from mclevelbase import appSupportDir, exhaust, ChunkNotPresent

log = logging.getLogger(__name__)

__author__ = 'Rio'

# Thank you, Stackoverflow
# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    def is_exe(f):
        return os.path.exists(f) and os.access(f, os.X_OK)

    fpath, _fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        if sys.platform == "win32":
            if "SYSTEMROOT" in os.environ:
                root = os.environ["SYSTEMROOT"]
                exe_file = os.path.join(root, program)
                if is_exe(exe_file):
                    return exe_file
        if "PATH" in os.environ:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

    return None


convert = lambda text: int(text) if text.isdigit() else text
alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]


def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)


class ServerJarStorage(object):
    defaultCacheDir = os.path.join(appSupportDir, u"ServerJarStorage")

    def __init__(self, cacheDir=None):
        if cacheDir is None:
            cacheDir = self.defaultCacheDir

        self.cacheDir = cacheDir

        if not os.path.exists(self.cacheDir):
            os.makedirs(self.cacheDir)
        readme = os.path.join(self.cacheDir, "README.TXT")
        if not os.path.exists(readme):
            with file(readme, "w") as f:
                f.write("""
About this folder:

This folder is used by MCEdit and pymclevel to store different versions of the
Minecraft Server to use for terrain generation. It should have one or more
subfolders, one for each version of the server. Each subfolder must hold at
least one file named minecraft_server.jar, and the subfolder's name should
have the server's version plus the names of any installed mods.

There may already be a subfolder here (for example, "Beta 1.7.3") if you have
used the Chunk Create feature in MCEdit to create chunks using the server.

Version numbers can be automatically detected. If you place one or more
minecraft_server.jar files in this folder, they will be placed automatically
into well-named subfolders the next time you run MCEdit. If a file's name
begins with "minecraft_server" and ends with ".jar", it will be detected in
this way.
""")

        self.reloadVersions()

    def reloadVersions(self):
        cacheDirList = os.listdir(self.cacheDir)
        self.versions = list(reversed(sorted([v for v in cacheDirList if os.path.exists(self.jarfileForVersion(v))], key=alphanum_key)))

        if MCServerChunkGenerator.javaExe:
            for f in cacheDirList:
                p = os.path.join(self.cacheDir, f)
                if f.startswith("minecraft_server") and f.endswith(".jar") and os.path.isfile(p):
                    print "Unclassified minecraft_server.jar found in cache dir. Discovering version number..."
                    self.cacheNewVersion(p)
                    os.remove(p)

        print "Minecraft_Server.jar storage initialized."
        print u"Each server is stored in a subdirectory of {0} named with the server's version number".format(self.cacheDir)

        print "Cached servers: ", self.versions

    def downloadCurrentServer(self):
        print "Downloading the latest Minecraft Server..."
        try:
            (filename, headers) = urllib.urlretrieve("http://www.minecraft.net/download/minecraft_server.jar")
        except Exception, e:
            print "Error downloading server: {0!r}".format(e)
            return

        self.cacheNewVersion(filename, allowDuplicate=False)

    def cacheNewVersion(self, filename, allowDuplicate=True):
        """ Finds the version number from the server jar at filename and copies
        it into the proper subfolder of the server jar cache folder"""

        version = MCServerChunkGenerator._serverVersionFromJarFile(filename)
        print "Found version ", version
        versionDir = os.path.join(self.cacheDir, version)

        i = 1
        newVersionDir = versionDir
        while os.path.exists(newVersionDir):
            if not allowDuplicate:
                return

            newVersionDir = versionDir + " (" + str(i) + ")"
            i += 1

        os.mkdir(newVersionDir)

        shutil.copy2(filename, os.path.join(newVersionDir, "minecraft_server.jar"))

        if version not in self.versions:
            self.versions.append(version)

    def jarfileForVersion(self, v):
        return os.path.join(self.cacheDir, v, "minecraft_server.jar").encode(sys.getfilesystemencoding())

    def checksumForVersion(self, v):
        jf = self.jarfileForVersion(v)
        with file(jf, "rb") as f:
            import hashlib
            return hashlib.md5(f.read()).hexdigest()

    broken_versions = ["Beta 1.9 Prerelease {0}".format(i) for i in (1, 2, 3)]

    @property
    def latestVersion(self):
        if len(self.versions) == 0:
            return None
        return max((v for v in self.versions if v not in self.broken_versions), key=alphanum_key)

    def getJarfile(self, version=None):
        if len(self.versions) == 0:
            print "No servers found in cache."
            self.downloadCurrentServer()

        version = version or self.latestVersion
        if version not in self.versions:
            return None
        return self.jarfileForVersion(version)


class JavaNotFound(RuntimeError):
    pass


class VersionNotFound(RuntimeError):
    pass


def readProperties(filename):
    if not os.path.exists(filename):
        return {}

    with file(filename) as f:
        properties = dict((line.split("=", 2) for line in (l.strip() for l in f) if not line.startswith("#")))

    return properties


def saveProperties(filename, properties):
    with file(filename, "w") as f:
        for k, v in properties.iteritems():
            f.write("{0}={1}\n".format(k, v))


def findJava():
    if sys.platform == "win32":
        javaExe = which("java.exe")
        if javaExe is None:
            KEY_NAME = "HKLM\SOFTWARE\JavaSoft\Java Runtime Environment"
            try:
                p = subprocess.Popen(["REG", "QUERY", KEY_NAME, "/v", "CurrentVersion"], stdout=subprocess.PIPE, universal_newlines=True)
                o, e = p.communicate()
                lines = o.split("\n")
                for l in lines:
                    l = l.strip()
                    if l.startswith("CurrentVersion"):
                        words = l.split(None, 2)
                        version = words[-1]
                        p = subprocess.Popen(["REG", "QUERY", KEY_NAME + "\\" + version, "/v", "JavaHome"], stdout=subprocess.PIPE, universal_newlines=True)
                        o, e = p.communicate()
                        lines = o.split("\n")
                        for l in lines:
                            l = l.strip()
                            if l.startswith("JavaHome"):
                                w = l.split(None, 2)
                                javaHome = w[-1]
                                javaExe = os.path.join(javaHome, "bin", "java.exe")
                                print "RegQuery: java.exe found at ", javaExe
                                break

            except Exception, e:
                print "Error while locating java.exe using the Registry: ", repr(e)
    else:
        javaExe = which("java")

    return javaExe


class MCServerChunkGenerator(object):
    """Generates chunks using minecraft_server.jar. Uses a ServerJarStorage to
    store different versions of minecraft_server.jar in an application support
    folder.

        from pymclevel import *

    Example usage:

        gen = MCServerChunkGenerator()  # with no arguments, use the newest
                                        # server version in the cache, or download
                                        # the newest one automatically
        level = loadWorldNamed("MyWorld")

        gen.generateChunkInLevel(level, 12, 24)


    Using an older version:

        gen = MCServerChunkGenerator("Beta 1.6.5")

    """
    defaultJarStorage = None

    javaExe = findJava()
    jarStorage = None
    tempWorldCache = {}

    def __init__(self, version=None, jarfile=None, jarStorage=None):

        self.jarStorage = jarStorage or self.getDefaultJarStorage()

        if self.javaExe is None:
            raise JavaNotFound("Could not find java. Please check that java is installed correctly. (Could not find java in your PATH environment variable.)")
        if jarfile is None:
            jarfile = self.jarStorage.getJarfile(version)
        if jarfile is None:
            raise VersionNotFound("Could not find minecraft_server.jar for version {0}. Please make sure that a minecraft_server.jar is placed under {1} in a subfolder named after the server's version number.".format(version or "(latest)", self.jarStorage.cacheDir))
        self.serverJarFile = jarfile
        self.serverVersion = version or self._serverVersion()

    @classmethod
    def getDefaultJarStorage(cls):
        if cls.defaultJarStorage is None:
            cls.defaultJarStorage = ServerJarStorage()
        return cls.defaultJarStorage

    @classmethod
    def clearWorldCache(cls):
        cls.tempWorldCache = {}

        for tempDir in os.listdir(cls.worldCacheDir):
            t = os.path.join(cls.worldCacheDir, tempDir)
            if os.path.isdir(t):
                shutil.rmtree(t)

    def createReadme(self):
        readme = os.path.join(self.worldCacheDir, "README.TXT")

        if not os.path.exists(readme):
            with file(readme, "w") as f:
                f.write("""
    About this folder:

    This folder is used by MCEdit and pymclevel to cache levels during terrain
    generation. Feel free to delete it for any reason.
    """)

    worldCacheDir = os.path.join(tempfile.gettempdir(), "pymclevel_MCServerChunkGenerator")

    def tempWorldForLevel(self, level):

        # tempDir = tempfile.mkdtemp("mclevel_servergen")
        tempDir = os.path.join(self.worldCacheDir, self.jarStorage.checksumForVersion(self.serverVersion), str(level.RandomSeed))
        propsFile = os.path.join(tempDir, "server.properties")
        properties = readProperties(propsFile)

        tempWorld = self.tempWorldCache.get((self.serverVersion, level.RandomSeed))

        if tempWorld is None:
            if not os.path.exists(tempDir):
                os.makedirs(tempDir)
                self.createReadme()

            worldName = "world"
            worldName = properties.setdefault("level-name", worldName)

            tempWorldDir = os.path.join(tempDir, worldName)
            tempWorld = infiniteworld.MCInfdevOldLevel(tempWorldDir, create=True, random_seed=level.RandomSeed)
            tempWorld.close()

            tempWorldRO = infiniteworld.MCInfdevOldLevel(tempWorldDir, readonly=True)

            self.tempWorldCache[self.serverVersion, level.RandomSeed] = tempWorldRO

        if level.dimNo == 0:
            properties["allow-nether"] = "false"
        else:
            tempWorld = tempWorld.getDimension(level.dimNo)

            properties["allow-nether"] = "true"

        properties["server-port"] = int(32767 + random.random() * 32700)
        saveProperties(propsFile, properties)

        return tempWorld, tempDir

    def generateAtPosition(self, tempWorld, tempDir, cx, cz):
        return exhaust(self.generateAtPositionIter(tempWorld, tempDir, cx, cz))

    def generateAtPositionIter(self, tempWorld, tempDir, cx, cz, simulate=False):
        tempWorldRW = infiniteworld.MCInfdevOldLevel(tempWorld.filename)
        tempWorldRW.setPlayerSpawnPosition((cx * 16, 64, cz * 16))
        tempWorldRW.saveInPlace()
        tempWorldRW.close()
        del tempWorldRW

        tempWorld.unload()

        startTime = time.time()
        proc = self.runServer(tempDir)
        while proc.poll() is None:
            line = proc.stderr.readline().strip()
            log.info(line)
            yield line

#            Forge and FML change stderr output, causing MCServerChunkGenerator to wait endlessly.
#
#            Vanilla:
#              2012-11-13 11:29:19 [INFO] Done (9.962s)!
#
#            Forge/FML:
#              2012-11-13 11:47:13 [INFO] [Minecraft] Done (8.020s)!

            if "[INFO]" in line and "Done" in line:
                if simulate:
                    duration = time.time() - startTime

                    simSeconds = max(8, int(duration) + 1)

                    for i in range(simSeconds):
                        # process tile ticks
                        yield "%2d/%2d: Simulating the world for a little bit..." % (i, simSeconds)
                        time.sleep(1)

                proc.stdin.write("stop\n")
                proc.wait()
                break
            if "FAILED TO BIND" in line:
                proc.kill()
                proc.wait()
                raise RuntimeError("Server failed to bind to port!")

        stdout, _ = proc.communicate()

        if "Could not reserve enough space" in stdout and not MCServerChunkGenerator.lowMemory:
            MCServerChunkGenerator.lowMemory = True
            for i in self.generateAtPositionIter(tempWorld, tempDir, cx, cz):
                yield i

        (tempWorld.parentWorld or tempWorld).loadLevelDat()  # reload version number

    def copyChunkAtPosition(self, tempWorld, level, cx, cz):
        if level.containsChunk(cx, cz):
            return
        try:
            tempChunkBytes = tempWorld._getChunkBytes(cx, cz)
        except ChunkNotPresent, e:
            raise ChunkNotPresent, "While generating a world in {0} using server {1} ({2!r})".format(tempWorld, self.serverJarFile, e), sys.exc_info()[2]

        level.worldFolder.saveChunk(cx, cz, tempChunkBytes)
        level._allChunks = None

    def generateChunkInLevel(self, level, cx, cz):
        assert isinstance(level, infiniteworld.MCInfdevOldLevel)

        tempWorld, tempDir = self.tempWorldForLevel(level)
        self.generateAtPosition(tempWorld, tempDir, cx, cz)
        self.copyChunkAtPosition(tempWorld, level, cx, cz)

    minRadius = 5
    maxRadius = 20

    def createLevel(self, level, box, simulate=False, **kw):
        return exhaust(self.createLevelIter(level, box, simulate, **kw))

    def createLevelIter(self, level, box, simulate=False, **kw):
        if isinstance(level, basestring):
            filename = level
            level = infiniteworld.MCInfdevOldLevel(filename, create=True, **kw)

        assert isinstance(level, infiniteworld.MCInfdevOldLevel)
        minRadius = self.minRadius

        genPositions = list(itertools.product(
                       xrange(box.mincx, box.maxcx, minRadius * 2),
                       xrange(box.mincz, box.maxcz, minRadius * 2)))

        for i, (cx, cz) in enumerate(genPositions):
            log.info("Generating at %s" % ((cx, cz),))
            parentDir = dirname(os.path.abspath(level.worldFolder.filename))
            propsFile = join(parentDir, "server.properties")
            props = readProperties(join(dirname(self.serverJarFile), "server.properties"))
            props["level-name"] = basename(level.worldFolder.filename)
            props["server-port"] = int(32767 + random.random() * 32700)
            saveProperties(propsFile, props)

            for p in self.generateAtPositionIter(level, parentDir, cx, cz, simulate):
                yield i, len(genPositions), p

        level.close()

    def generateChunksInLevel(self, level, chunks):
        return exhaust(self.generateChunksInLevelIter(level, chunks))

    def generateChunksInLevelIter(self, level, chunks, simulate=False):
        tempWorld, tempDir = self.tempWorldForLevel(level)

        startLength = len(chunks)
        minRadius = self.minRadius
        maxRadius = self.maxRadius
        chunks = set(chunks)

        while len(chunks):
            length = len(chunks)
            centercx, centercz = chunks.pop()
            chunks.add((centercx, centercz))
            # assume the generator always generates at least an 11x11 chunk square.
            centercx += minRadius
            centercz += minRadius

            # boxedChunks = [cPos for cPos in chunks if inBox(cPos)]

            print "Generating {0} chunks out of {1} starting from {2}".format("XXX", len(chunks), (centercx, centercz))
            yield startLength - len(chunks), startLength

            # chunks = [c for c in chunks if not inBox(c)]

            for p in self.generateAtPositionIter(tempWorld, tempDir, centercx, centercz, simulate):
                yield startLength - len(chunks), startLength, p

            i = 0
            for cx, cz in itertools.product(
                            xrange(centercx - maxRadius, centercx + maxRadius),
                            xrange(centercz - maxRadius, centercz + maxRadius)):
                if level.containsChunk(cx, cz):
                    chunks.discard((cx, cz))
                elif ((cx, cz) in chunks
                    and all(tempWorld.containsChunk(ncx, ncz) for ncx, ncz in itertools.product(xrange(cx-1, cx+2), xrange(cz-1, cz+2)))
                    ):
                    self.copyChunkAtPosition(tempWorld, level, cx, cz)
                    i += 1
                    chunks.discard((cx, cz))
                    yield startLength - len(chunks), startLength

            if length == len(chunks):
                print "No chunks were generated. Aborting."
                break

        level.saveInPlace()

    def runServer(self, startingDir):
        if isinstance(startingDir, unicode):
            startingDir = startingDir.encode(sys.getfilesystemencoding())

        return self._runServer(startingDir, self.serverJarFile)

    lowMemory = False

    @classmethod
    def _runServer(cls, startingDir, jarfile):
        log.info("Starting server %s in %s", jarfile, startingDir)
        if cls.lowMemory:
            memflags = []
        else:
            memflags = ["-Xmx1024M", "-Xms1024M", ]

        proc = subprocess.Popen([cls.javaExe, "-Djava.awt.headless=true"] + memflags + ["-jar", jarfile],
            executable=cls.javaExe,
            cwd=startingDir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            )
        return proc

    def _serverVersion(self):
        return self._serverVersionFromJarFile(self.serverJarFile)

    @classmethod
    def _serverVersionFromJarFile(cls, jarfile):
        tempdir = tempfile.mkdtemp("mclevel_servergen")
        proc = cls._runServer(tempdir, jarfile)

        version = "Unknown"
        # out, err = proc.communicate()
        # for line in err.split("\n"):

        while proc.poll() is None:
            line = proc.stderr.readline()
            if "Preparing start region" in line:
                break
            if "Starting minecraft server version" in line:
                version = line.split("Starting minecraft server version")[1].strip()
                break

        if proc.returncode is None:
            try:
                proc.kill()
            except WindowsError:
                pass  # access denied, process already terminated

        proc.wait()
        shutil.rmtree(tempdir)
        if ";)" in version:
            version = version.replace(";)", "")  # Damnit, Jeb!
        # Versions like "0.2.1" are alphas, and versions like "1.0.0" without "Beta" are releases
        if version[0] == "0":
            version = "Alpha " + version
        try:
            if int(version[0]) > 0:
                version = "Release " + version
        except ValueError:
            pass

        return version
