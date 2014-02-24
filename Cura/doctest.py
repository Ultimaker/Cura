"""
A helper file to check which parts of the code have documentation and which are lacking documentation.
This because much of the Cura code is currently undocumented which needs to be improved.
"""
import os
import traceback
import glob
import sys
import inspect
import types
import random

def treeWalk(moduleList, dirname, fnames):
	""" Callback from the os.path.walk function, see if the given path is a module and import it to put it in the moduleList """
	dirname = dirname.replace("\\", ".").replace("/", ".")
	if dirname.startswith('Cura.gui'):
		return
	if dirname == 'Cura.util.pymclevel':
		return
	if dirname == 'Cura.util.Power':
		return
	if dirname == 'Cura.plugins':
		return
	if dirname == 'Cura.resouces':
		return
	for moduleName in filter(lambda f: f.endswith('.py'), fnames):
		moduleName = moduleName[:-3]
		if moduleName == '__init__':
			continue
		fullName = '%s.%s' % (dirname, moduleName)
		try:
			module = __import__(fullName, fromlist=['Cura'], level=1)
			moduleList.append(module)
		except:
			#traceback.print_exc()
			print "Failed to load: %s" % (fullName)

def main():
	"""
	Main doctest function.
	Calculate how many things are documented and not documented yet.
	And report a random selection of undocumented functions/ modules.
	"""
	moduleList = []
	os.path.walk("Cura", treeWalk, moduleList)
	moduleDocCount = 0
	functionCount = 0
	functionDocCount = 0
	memberCount = 0
	memberDocCount = 0
	typeCount = 0
	typeDocCount = 0
	undocList = []
	for module in moduleList:
		if inspect.getdoc(module):
			moduleDocCount += 1
		else:
			undocList.append(module.__name__)
		for name in dir(module):
			a = getattr(module, name)
			try:
				if not inspect.getfile(a).startswith('Cura'):
					continue
			except:
				continue
			if type(a) is types.FunctionType:
				functionCount += 1
				if inspect.getdoc(a):
					functionDocCount += 1
				else:
					undocList.append('%s.%s' % (module.__name__, name))
			elif type(a) is types.TypeType:
				typeCount += 1
				if inspect.getdoc(a):
					typeDocCount += 1
				else:
					undocList.append('%s.%s' % (module.__name__, name))
				for name2 in dir(a):
					a2 = getattr(a, name2)
					if type(a2) is types.MethodType:
						if hasattr(a.__bases__[0], name2):
							continue
						memberCount += 1
						if inspect.getdoc(a2):
							memberDocCount += 1
						# else:
						# 	undocList.append('%s.%s.%s' % (module.__name__, name, name2))

	print '%d/%d modules have documentation.' % (moduleDocCount, len(moduleList))
	print '%d/%d types have documentation.' % (typeDocCount, typeCount)
	print '%d/%d functions have documentation.' % (functionDocCount, functionCount)
	print '%d/%d member functions have documentation.' % (memberDocCount, memberCount)
	print '%.1f%% documented.' % (float(moduleDocCount + functionDocCount + typeDocCount + memberDocCount) / float(len(moduleList) + functionCount + typeCount + memberCount) * 100.0)
	print ''
	print 'You might want to document:'
	for n in xrange(0, 10):
		print random.Random().choice(undocList)

if __name__ == '__main__':
	main()
