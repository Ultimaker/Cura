import cStringIO as StringIO

class BigDataStorage(object):
	"""
	The StringIO from python aborts with an out-of-memory error after 250MB.
	So the BigDataStorage stores data in multiple StringIOs to prevent this issue.
	"""
	def __init__(self):
		self._active = StringIO.StringIO()
		self._list = [self._active]
		self._read_index = None

	def write(self, data):
		self._active.write(data)
		if self._active.tell() > 1024 * 1024 * 100:
			self._active = StringIO.StringIO()
			self._list.append(self._active)

	def seekStart(self):
		self._active = self._list[0]
		self._active.seek(0)
		self._read_index = 0

	def read(self, size=None):
		ret = self._active.read(size)
		if ret == '':
			if self._read_index + 1 < len(self._list):
				self._read_index += 1
				self._active = self._list[self._read_index]
				self._active.seek(0)
				ret = self._active.read(size)
		return ret

	def replaceAtStart(self, key, value):
		data = self._list[0].getvalue()
		block0 = data[0:2048]
		value = (value + ' ' * len(key))[:len(key)]
		block0 = block0.replace(key, value)
		self._list[0] = StringIO.StringIO()
		self._list[0].write(block0)
		self._list[0].write(data[2048:])

	def __len__(self):
		ret = 0
		for data in self._list:
			pos = data.tell()
			data.seek(0, 2)
			ret += data.tell()
			data.seek(pos)
		return ret

	def __iter__(self):
		self._iter_index = 0
		return self

	def next(self):
		if self._iter_index < len(self._list):
			ret = self._list[self._iter_index].readline()
			if ret == '':
				self._iter_index += 1
				if self._iter_index < len(self._list):
					self._list[self._iter_index].seek(0)
				return self.next()
			return ret
		raise StopIteration

	def tell(self):
		pos = 0
		for data in self._list[:self._iter_index]:
			pos += data.tell()
		if self._iter_index < len(self._list):
			pos += self._list[self._iter_index].tell()
		return pos

	def clone(self):
		clone = BigDataStorage()
		clone._list = []
		for item in self._list:
			clone._list.append(StringIO.StringIO(item.getvalue()))
		clone._active = clone._list[-1]
		return clone