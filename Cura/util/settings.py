__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

class setting(object):
	def __init__(self, key, name, description):
		self._key = key
		self._name = name
		self._description = description
