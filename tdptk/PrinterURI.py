#	tdptk - 3d Printing Toolkit
#	Copyright (C) 2021-2021 Johannes Bauer
#
#	This file is part of tdptk.
#
#	tdptk is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	tdptk is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with tdptk; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import enum
import urllib.parse

class PrinterProtocol(enum.Enum):
	FlashForge = "ff"

class PrinterURI():
	def __init__(self, protocol, host, port):
		assert(isinstance(protocol, PrinterProtocol))
		assert(isinstance(port, int))
		self._protocol = protocol
		self._host = host
		self._port = port

	@classmethod
	def parse(cls, uri):
		parsed = urllib.parse.urlparse(uri)
		protocol = PrinterProtocol(parsed.scheme)
		if ":" in parsed.netloc:
			(host, port) = parsed.netloc.split(":", maxsplit = 1)
			port = int(port)
		else:
			host = parsed.netloc
			port = {
				PrinterProtocol.FlashForge:		8899,
			}[protocol]
		return cls(protocol = protocol, host = host, port = port)

	@property
	def protocol(self):
		return self._protocol

	@property
	def host(self):
		return self._host

	@property
	def port(self):
		return self._port
