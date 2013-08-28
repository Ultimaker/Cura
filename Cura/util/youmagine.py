from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import json
import httplib as httpclient
import urllib

class httpUploadDataStream(object):
	def __init__(self, progressCallback):
		self._dataList = []
		self._totalLength = 0
		self._readPos = 0
		self._progressCallback = progressCallback

	def write(self, data):
		size = len(data)
		if size < 1:
			return
		blocks = size / 2048
		for n in xrange(0, blocks):
			self._dataList.append(data[n*2048:n*2048+2048])
		self._dataList.append(data[blocks*2048:])
		self._totalLength += size

	def read(self, size):
		if self._readPos >= len(self._dataList):
			return None
		ret = self._dataList[self._readPos]
		self._readPos += 1
		if self._progressCallback is not None:
			self._progressCallback(float(self._readPos / len(self._dataList)))
		return ret

	def __len__(self):
		return self._totalLength

class Youmagine(object):
	def __init__(self, authToken, progressCallback = None):
		self._hostUrl = 'api.youmagine.com'
		self._viewUrl = 'www.youmagine.com'
		self._authUrl = 'https://www.youmagine.com/integrations/cura/authorized_integrations/new'
		self._authToken = authToken
		self._userName = None
		self._userID = None
		self._http = None
		self._hostReachable = True
		self._progressCallback = progressCallback
		self._categories = [
			('Art', 2),
			('Fashion', 3),
			('For your home', 4),
			('Gadget', 5),
			('Games', 6),
			('Jewelry', 7),
			('Maker/DIY', 8),
			('Miniatures', 9),
			('Other', 1),
		]
		self._licenses = [
			('Creative Commons - Share Alike', 'cc'),
			('Creative Commons - Attribution-NonCommercial-ShareAlike', 'ccnc'),
			('GPLv3', 'gplv3'),
		]

	def getAuthorizationUrl(self):
		return self._authUrl

	def getCategories(self):
		return map(lambda n: n[0], self._categories)

	def getLicenses(self):
		return map(lambda n: n[0], self._licenses)

	def setAuthToken(self, token):
		self._authToken = token
		self._userName = None
		self._userID = None

	def getAuthToken(self):
		return self._authToken

	def isHostReachable(self):
		return self._hostReachable

	def viewUrlForDesign(self, id):
		return 'https://%s/designs/%d' % (self._viewUrl, id)

	def editUrlForDesign(self, id):
		return 'https://%s/designs/%d/edit' % (self._viewUrl, id)

	def isAuthorized(self):
		if self._authToken is None:
			return False
		if self._userName is None:
			#No username yet, try to request the username to see if the authToken is valid.
			result = self._request('GET', '/authorized_integrations/%s/whoami.json' % (self._authToken))

			if 'error' in result:
				self._authToken = None
				return False
			self._userName = result['screen_name']
			self._userID = result['id']
		return True

	def createDesign(self, name, description, category, license):
		res = self._request('POST', '/designs.json', {'design[name]': name, 'design[excerpt]': description, 'design[design_category_id]': filter(lambda n: n[0] == category, self._categories)[0][1], 'design[license]': filter(lambda n: n[0] == license, self._licenses)[0][1]})
		if 'id' in res:
			return res['id']
		print res
		return None

	def publishDesign(self, id):
		res = self._request('PUT', '/designs/%d/mark_as/publish.json' % (id), {'ignore': 'me'})
		if res is not None:
			return False
		return True

	def createDocument(self, designId, name, contents):
		res = self._request('POST', '/designs/%d/documents.json' % (designId), {'document[name]': name, 'document[description]': 'Uploaded from Cura'}, {'document[file]': (name, contents)})
		if 'id' in res:
			return res['id']
		print res
		return None

	def createImage(self, designId, name, contents):
		res = self._request('POST', '/designs/%d/images.json' % (designId), {'image[name]': name, 'image[description]': 'Uploaded from Cura'}, {'image[file]': (name, contents)})
		if 'id' in res:
			return res['id']
		print res
		return None

	def listDesigns(self):
		res = self._request('GET', '/users/%s/designs.json' % (self._userID))
		return res

	def _request(self, method, url, postData = None, files = None):
		retryCount = 2
		if self._authToken is not None:
			url += '?auth_token=%s' % (self._authToken)
		error = 'Failed to connect to %s' % self._hostUrl
		for n in xrange(0, retryCount):
			if self._http is None:
				self._http = httpclient.HTTPSConnection(self._hostUrl)
			try:
				if files is not None:
					boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
					s = httpUploadDataStream(self._progressCallback)
					for k, v in files.iteritems():
						filename = v[0]
						fileContents = v[1]
						s.write('--%s\r\n' % (boundary))
						s.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (k, filename))
						s.write('Content-Type: application/octet-stream\r\n')
						s.write('Content-Transfer-Encoding: binary\r\n')
						s.write('\r\n')
						s.write(fileContents)
						s.write('\r\n')

					for k, v in postData.iteritems():
						s.write('--%s\r\n' % (boundary))
						s.write('Content-Disposition: form-data; name="%s"\r\n' % (k))
						s.write('\r\n')
						s.write(str(v))
						s.write('\r\n')
					s.write('--%s--\r\n' % (boundary))

					self._http.request(method, url, s, {"Content-type": "multipart/form-data; boundary=%s" % (boundary), "Content-Length": len(s)})
				elif postData is not None:
					self._http.request(method, url, urllib.urlencode(postData), {"Content-type": "application/x-www-form-urlencoded"})
				else:
					self._http.request(method, url)
			except IOError:
				self._http.close()
				continue
			try:
				response = self._http.getresponse()
				responseText = response.read()
			except:
				self._http.close()
				continue
			try:
				if responseText == '':
					return None
				return json.loads(responseText)
			except ValueError:
				print response.getheaders()
				print responseText
				error = 'Failed to decode JSON response'
		self._hostReachable = False
		return {'error': error}


#Fake Youmagine class to test without internet
class FakeYoumagine(Youmagine):
	def __init__(self, authToken, callback):
		super(FakeYoumagine, self).__init__(authToken)
		self._authUrl = 'file:///C:/Models/output.html'
		self._authToken = None

	def isAuthorized(self):
		if self._authToken is None:
			return False
		if self._userName is None:
			self._userName = 'FakeYoumagine'
			self._userID = '1'
		return True

	def isHostReachable(self):
		return True

	def createDesign(self, name, description, category, license):
		return 1

	def publishDesign(self, id):
		pass

	def createDocument(self, designId, name, contents):
		print "Create document: %s" % (name)
		f = open("C:/models/%s" % (name), "wb")
		f.write(contents)
		f.close()
		return 1

	def createImage(self, designId, name, contents):
		print "Create image: %s" % (name)
		f = open("C:/models/%s" % (name), "wb")
		f.write(contents)
		f.close()
		return 1

	def listDesigns(self):
		return []

	def _request(self, method, url, postData = None, files = None):
		print "Err: Tried to do request: %s %s" % (method, url)

def main():
	ym = Youmagine('j3rY9kQF62ptuZF7vqbR')
	if not ym.isAuthorized():
		print "Failed to authorize"
		return
	for design in ym.listDesigns():
		print design['name']
