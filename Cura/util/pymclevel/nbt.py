
# vim:set sw=2 sts=2 ts=2:

"""
Named Binary Tag library. Serializes and deserializes TAG_* objects
to and from binary data. Load a Minecraft level by calling nbt.load().
Create your own TAG_* objects and set their values.
Save a TAG_* object to a file or StringIO object.

Read the test functions at the end of the file to get started.

This library requires Numpy.    Get it here:
http://new.scipy.org/download.html

Official NBT documentation is here:
http://www.minecraft.net/docs/NBT.txt


Copyright 2010 David Rio Vierra
"""
import collections
import gzip
import itertools
import logging
import struct
import zlib
from cStringIO import StringIO

import numpy
from numpy import array, zeros, fromstring


log = logging.getLogger(__name__)


class NBTFormatError(RuntimeError):
    pass


TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_SHORT_ARRAY = 12


class TAG_Value(object):
    """Simple values. Subclasses override fmt to change the type and size.
    Subclasses may set data_type instead of overriding setValue for automatic data type coercion"""
    __slots__ = ('_name', '_value')

    def __init__(self, value=0, name=""):
        self.value = value
        self.name = name

    fmt = struct.Struct("b")
    tagID = NotImplemented
    data_type = NotImplemented

    _name = None
    _value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newVal):
        """Change the TAG's value. Data types are checked and coerced if needed."""
        self._value = self.data_type(newVal)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, newVal):
        """Change the TAG's name. Coerced to a unicode."""
        self._name = unicode(newVal)

    @classmethod
    def load_from(cls, ctx):
        data = ctx.data[ctx.offset:]
        (value,) = cls.fmt.unpack_from(data)
        self = cls(value=value)
        ctx.offset += self.fmt.size
        return self

    def __repr__(self):
        return "<%s name=\"%s\" value=%r>" % (str(self.__class__.__name__), self.name, self.value)

    def write_tag(self, buf):
        buf.write(chr(self.tagID))

    def write_name(self, buf):
        if self.name is not None:
            write_string(self.name, buf)

    def write_value(self, buf):
        buf.write(self.fmt.pack(self.value))


class TAG_Byte(TAG_Value):
    __slots__ = ('_name', '_value')
    tagID = TAG_BYTE
    fmt = struct.Struct(">b")
    data_type = int


class TAG_Short(TAG_Value):
    __slots__ = ('_name', '_value')
    tagID = TAG_SHORT
    fmt = struct.Struct(">h")
    data_type = int


class TAG_Int(TAG_Value):
    __slots__ = ('_name', '_value')
    tagID = TAG_INT
    fmt = struct.Struct(">i")
    data_type = int


class TAG_Long(TAG_Value):
    __slots__ = ('_name', '_value')
    tagID = TAG_LONG
    fmt = struct.Struct(">q")
    data_type = long


class TAG_Float(TAG_Value):
    __slots__ = ('_name', '_value')
    tagID = TAG_FLOAT
    fmt = struct.Struct(">f")
    data_type = float


class TAG_Double(TAG_Value):
    __slots__ = ('_name', '_value')
    tagID = TAG_DOUBLE
    fmt = struct.Struct(">d")
    data_type = float


class TAG_Byte_Array(TAG_Value):
    """Like a string, but for binary data. Four length bytes instead of
    two. Value is a numpy array, and you can change its elements"""

    tagID = TAG_BYTE_ARRAY

    def __init__(self, value=None, name=""):
        if value is None:
            value = zeros(0, self.dtype)
        self.name = name
        self.value = value

    def __repr__(self):
        return "<%s name=%s length=%d>" % (self.__class__, self.name, len(self.value))

    __slots__ = ('_name', '_value')

    def data_type(self, value):
        return array(value, self.dtype)

    dtype = numpy.dtype('uint8')

    @classmethod
    def load_from(cls, ctx):
        data = ctx.data[ctx.offset:]
        (string_len,) = TAG_Int.fmt.unpack_from(data)
        value = fromstring(data[4:string_len * cls.dtype.itemsize + 4], cls.dtype)
        self = cls(value)
        ctx.offset += string_len * cls.dtype.itemsize + 4
        return self

    def write_value(self, buf):
        value_str = self.value.tostring()
        buf.write(struct.pack(">I%ds" % (len(value_str),), self.value.size, value_str))


class TAG_Int_Array(TAG_Byte_Array):
    """An array of big-endian 32-bit integers"""
    tagID = TAG_INT_ARRAY
    __slots__ = ('_name', '_value')
    dtype = numpy.dtype('>u4')



class TAG_Short_Array(TAG_Int_Array):
    """An array of big-endian 16-bit integers. Not official, but used by some mods."""
    tagID = TAG_SHORT_ARRAY
    __slots__ = ('_name', '_value')
    dtype = numpy.dtype('>u2')


class TAG_String(TAG_Value):
    """String in UTF-8
    The value parameter must be a 'unicode' or a UTF-8 encoded 'str'
    """

    tagID = TAG_STRING

    def __init__(self, value="", name=""):
        if name:
            self.name = name
        self.value = value

    _decodeCache = {}

    __slots__ = ('_name', '_value')

    def data_type(self, value):
        if isinstance(value, unicode):
            return value
        else:
            decoded = self._decodeCache.get(value)
            if decoded is None:
                decoded = value.decode('utf-8')
                self._decodeCache[value] = decoded

            return decoded


    @classmethod
    def load_from(cls, ctx):
        value = load_string(ctx)
        return cls(value)

    def write_value(self, buf):
        write_string(self._value, buf)

string_len_fmt = struct.Struct(">H")


def load_string(ctx):
    data = ctx.data[ctx.offset:]
    (string_len,) = string_len_fmt.unpack_from(data)

    value = data[2:string_len + 2].tostring()
    ctx.offset += string_len + 2
    return value


def write_string(string, buf):
    encoded = string.encode('utf-8')
    buf.write(struct.pack(">h%ds" % (len(encoded),), len(encoded), encoded))

#noinspection PyMissingConstructor


class TAG_Compound(TAG_Value, collections.MutableMapping):
    """A heterogenous list of named tags. Names must be unique within
    the TAG_Compound. Add tags to the compound using the subscript
    operator [].    This will automatically name the tags."""

    tagID = TAG_COMPOUND

    ALLOW_DUPLICATE_KEYS = False

    __slots__ = ('_name', '_value')

    def __init__(self, value=None, name=""):
        self.value = value or []
        self.name = name

    def __repr__(self):
        return "<%s name='%s' keys=%r>" % (str(self.__class__.__name__), self.name, self.keys())

    def data_type(self, val):
        for i in val:
            self.check_value(i)
        return list(val)

    def check_value(self, val):
        if not isinstance(val, TAG_Value):
            raise TypeError("Invalid type for TAG_Compound element: %s" % val.__class__.__name__)
        if not val.name:
            raise ValueError("Tag needs a name to be inserted into TAG_Compound: %s" % val)

    @classmethod
    def load_from(cls, ctx):
        self = cls()
        while ctx.offset < len(ctx.data):
            tag_type = ctx.data[ctx.offset]
            ctx.offset += 1

            if tag_type == 0:
                break

            tag_name = load_string(ctx)
            tag = tag_classes[tag_type].load_from(ctx)
            tag.name = tag_name

            self._value.append(tag)

        return self

    def save(self, filename_or_buf=None, compressed=True):
        """
        Save the TAG_Compound element to a file. Since this element is the root tag, it can be named.

        Pass a filename to save the data to a file. Pass a file-like object (with a read() method)
        to write the data to that object. Pass nothing to return the data as a string.
        """
        if self.name is None:
            self.name = ""

        buf = StringIO()
        self.write_tag(buf)
        self.write_name(buf)
        self.write_value(buf)
        data = buf.getvalue()

        if compressed:
            gzio = StringIO()
            gz = gzip.GzipFile(fileobj=gzio, mode='wb')
            gz.write(data)
            gz.close()
            data = gzio.getvalue()

        if filename_or_buf is None:
            return data

        if isinstance(filename_or_buf, basestring):
            f = file(filename_or_buf, "wb")
            f.write(data)
        else:
            filename_or_buf.write(data)

    def write_value(self, buf):
        for tag in self.value:
            tag.write_tag(buf)
            tag.write_name(buf)
            tag.write_value(buf)

        buf.write("\x00")

    # --- collection functions ---

    def __getitem__(self, key):
        # hits=filter(lambda x: x.name==key, self.value)
        # if(len(hits)): return hits[0]
        for tag in self.value:
            if tag.name == key:
                return tag
        raise KeyError("Key {0} not found in tag {1}".format(key, self))

    def __iter__(self):
        return itertools.imap(lambda x: x.name, self.value)

    def __contains__(self, key):
        return key in map(lambda x: x.name, self.value)

    def __len__(self):
        return self.value.__len__()

    def __setitem__(self, key, item):
        """Automatically wraps lists and tuples in a TAG_List, and wraps strings
        and unicodes in a TAG_String."""
        if isinstance(item, (list, tuple)):
            item = TAG_List(item)
        elif isinstance(item, basestring):
            item = TAG_String(item)

        item.name = key
        self.check_value(item)

        # remove any items already named "key".
        if not self.ALLOW_DUPLICATE_KEYS:
            self._value = filter(lambda x: x.name != key, self._value)

        self._value.append(item)

    def __delitem__(self, key):
        self.value.__delitem__(self.value.index(self[key]))

    def add(self, value):
        if value.name is None:
            raise ValueError("Tag %r must have a name." % value)

        self[value.name] = value

    def get_all(self, key):
        return [v for v in self._value if v.name == key]

class TAG_List(TAG_Value, collections.MutableSequence):
    """A homogenous list of unnamed data of a single TAG_* type.
    Once created, the type can only be changed by emptying the list
    and adding an element of the new type. If created with no arguments,
    returns a list of TAG_Compound

    Empty lists in the wild have been seen with type TAG_Byte"""

    tagID = 9

    def __init__(self, value=None, name="", list_type=TAG_BYTE):
        # can be created from a list of tags in value, with an optional
        # name, or created from raw tag data, or created with list_type
        # taken from a TAG class or instance

        self.name = name
        self.list_type = list_type
        self.value = value or []

    __slots__ = ('_name', '_value')


    def __repr__(self):
        return "<%s name='%s' list_type=%r length=%d>" % (self.__class__.__name__, self.name,
                                                          tag_classes[self.list_type],
                                                          len(self))

    def data_type(self, val):
        if val:
            self.list_type = val[0].tagID
        assert all([x.tagID == self.list_type for x in val])
        return list(val)



    @classmethod
    def load_from(cls, ctx):
        self = cls()
        self.list_type = ctx.data[ctx.offset]
        ctx.offset += 1

        (list_length,) = TAG_Int.fmt.unpack_from(ctx.data, ctx.offset)
        ctx.offset += TAG_Int.fmt.size

        for i in range(list_length):
            tag = tag_classes[self.list_type].load_from(ctx)
            self.append(tag)

        return self


    def write_value(self, buf):
       buf.write(chr(self.list_type))
       buf.write(TAG_Int.fmt.pack(len(self.value)))
       for i in self.value:
           i.write_value(buf)

    def check_tag(self, value):
        if value.tagID != self.list_type:
            raise TypeError("Invalid type %s for TAG_List(%s)" % (value.__class__, tag_classes[self.list_type]))

    # --- collection methods ---

    def __iter__(self):
        return iter(self.value)

    def __contains__(self, tag):
        return tag in self.value

    def __getitem__(self, index):
        return self.value[index]

    def __len__(self):
        return len(self.value)

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            for tag in value:
                self.check_tag(tag)
        else:
            self.check_tag(value)

        self.value[index] = value

    def __delitem__(self, index):
        del self.value[index]

    def insert(self, index, value):
        if len(self) == 0:
            self.list_type = value.tagID
        else:
            self.check_tag(value)

        value.name = ""
        self.value.insert(index, value)


tag_classes = { c.tagID: c for c in (TAG_Byte, TAG_Short, TAG_Int, TAG_Long, TAG_Float, TAG_Double, TAG_String,
    TAG_Byte_Array, TAG_List, TAG_Compound, TAG_Int_Array, TAG_Short_Array) }



def gunzip(data):
    return gzip.GzipFile(fileobj=StringIO(data)).read()


def try_gunzip(data):
    try:
        data = gunzip(data)
    except IOError, zlib.error:
        pass
    return data


def load(filename="", buf=None):
    """
    Unserialize data from an NBT file and return the root TAG_Compound object. If filename is passed,
    reads from the file, otherwise uses data from buf. Buf can be a buffer object with a read() method or a string
    containing NBT data.
    """
    if filename:
        buf = file(filename, "rb")

    if hasattr(buf, "read"):
        buf = buf.read()

    return _load_buffer(try_gunzip(buf))

class load_ctx(object):
    pass

def _load_buffer(buf):
    if isinstance(buf, str):
        buf = fromstring(buf, 'uint8')
    data = buf

    if not len(data):
        raise NBTFormatError("Asked to load root tag of zero length")

    tag_type = data[0]
    if tag_type != 10:
        magic = data[:4]
        raise NBTFormatError('Not an NBT file with a root TAG_Compound '
                             '(file starts with "%s" (0x%08x)' % (magic.tostring(), magic.view(dtype='uint32')))

    ctx = load_ctx()
    ctx.offset = 1
    ctx.data = data

    tag_name = load_string(ctx)
    tag = TAG_Compound.load_from(ctx)
    tag.name = tag_name

    return tag


__all__ = [a.__name__ for a in tag_classes.itervalues()] + ["load", "gunzip"]

import nbt_util

TAG_Value.__str__ = nbt_util.nested_string

try:
    #noinspection PyUnresolvedReferences
    from _nbt import (load, TAG_Byte, TAG_Short, TAG_Int, TAG_Long, TAG_Float, TAG_Double, TAG_String,
    TAG_Byte_Array, TAG_List, TAG_Compound, TAG_Int_Array, TAG_Short_Array, NBTFormatError)
except ImportError:
    pass

