import socket, io, struct, blocks, time
from twisted.python import log
from threading import Thread

shipList = {
	12100 : "210.189.208.1",
	12200 : "210.189.208.16",
	12300 : "210.189.208.31",
	12400 : "210.189.208.46",
	12500 : "210.189.208.61",
	12600 : "210.189.208.76",
	12700 : "210.189.208.91",
	12800 : "210.189.208.106",
	12900 : "210.189.208.121",
	12000 : "210.189.208.136",
}

class BlockScrapingManager(object):
	def __init__(self):
		self.bline = BlockLine()
		self.bline.start()

	def getInLine(self, shipIp, shipPort, dstIp):
		identifier = self.bline.getNextIdentifier()
		self.bline.requests.append({'identifier': identifier, 'shipIp': shipIp, 'shipPort': shipPort, 'dstIp': dstIp})
		print("[BlockLine] Request #%i got in line." % identifier)
		while identifier not in self.bline.results:
			time.sleep(1)
		prize = self.bline.results[identifier]
		print("[BlockLine] Request #%i got their prize." % identifier)
		del self.bline.results[identifier]
		return prize

	def killBline(self):
		self.bline.active = False
	


class BlockLine(Thread):
	def __init__(self):
		super(BlockLine, self).__init__()
		self.requests = []
		self.results = {}
		self.identifier = 0
		self.active = True

	def run(self):
		print("[BlockLine] Thread started.")
		while self.active:
			if len(self.requests) > 0:
				currReq = self.requests.pop(0)
				print("[BlockLine] Starting on request #%i" % currReq['identifier'])
				data = scrapeBlockPacket(currReq['shipIp'], currReq['shipPort'], currReq['dstIp'])
				self.results[currReq['identifier']] = data
				print("[BlockLine] Finished request #%i, taking a nap." % currReq['identifier'])
				time.sleep(4)
			else:
				time.sleep(1)
		print("[BlockLine] Thread ended.")

	def getNextIdentifier(self):
		self.identifier = self.identifier + 1
		return self.identifier
		



def scrapeBlockPacket(shipIp, shipPort, dstIp):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	log.msg("[BlockQuery] Scraping %s:%i for a initial block..." % (shipIp, shipPort))
	s.connect((shipIp, shipPort))
	data = io.BytesIO()
	data.write(s.recv(4))
	realsize = struct.unpack_from('i', data.getvalue(), 0x0)[0]
	data.write(s.recv(realsize - 4))
	s.close()
	data.flush()
	data = bytearray(data.getvalue())
	name = data[0x24:0x64].decode('utf-16le')
	o1, o2, o3, o4, port = struct.unpack_from('BBBBH', buffer(data), 0x64)
	ipStr = '%i.%i.%i.%i' % (o1, o2, o3, o4)
	if port not in blocks.blockList:
		log.msg("[BlockList] Discovered new block %s at addr %s:%i! Recording..." % (name, ipStr, port))
		blocks.blockList[port] = (ipStr, name)
	o1, o2, o3, o4 = dstIp.split(".")
	struct.pack_into('BBBB', data, 0x64, int(o1), int(o2), int(o3), int(o4))
	return str(data)

manager = BlockScrapingManager()

def scrapeShipPacket(shipIp, shipPort, dstIp):
	o1, o2, o3, o4 = dstIp.split(".")
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	log.msg("[ShipQuery] Scraping %s:%i for ship status..." % (shipIp, shipPort))
	s.connect((shipIp, shipPort))
	data = io.BytesIO()
	data.write(s.recv(4))
	realsize = struct.unpack_from('i', data.getvalue(), 0x0)[0]
	data.write(s.recv(realsize - 4))
	s.close()
	data.flush()
	data = bytearray(data.getvalue())
	#Hardcoded ship count, fix this!
	pos = 0x10
	for x in xrange(1,10):
		struct.pack_into('BBBB', data, pos+0x20, int(o1), int(o2), int(o3), int(o4))
		pos += 0x34
	return str(data)
