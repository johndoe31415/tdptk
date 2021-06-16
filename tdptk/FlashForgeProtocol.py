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

import time
import re
import socket
import collections
import zlib
from .MultiRegex import MultiRegex, NoRegexMatchedException
from .ReceiveBuffer import ReceiveBuffer
from .Exceptions import PrinterCommunicationException
from .NamedStruct import NamedStruct

class FlashForgeCommunicationException(PrinterCommunicationException): pass

class GCodeChunk():
	_CHUNK_MAGIC = 0x5a5aa5a5

	ChunkFrame = NamedStruct((
		("L",		"magic"),
		("L",		"index"),
		("L",		"length"),
		("L",		"crc"),
		("4096s",	"data"),
	), struct_extra = ">")

	def __init__(self, chunk_index, chunk_data):
		self._index = chunk_index
		self._data = chunk_data

	def __bytes__(self):
		data = {
			"magic":	self._CHUNK_MAGIC,
			"index":	self._index,
			"length":	len(self._data),
			"crc":		zlib.crc32(self._data),
			"data":		self._data,
		}
		return self.ChunkFrame.pack(data)

class FlashForgeProtocol():
	_MachineInformation = collections.namedtuple("MachineInformation", [ "machine_type", "machine_name", "firmware", "serial_number", "dimension_x", "dimension_y", "dimension_z", "tool_count", "mac_address" ])
	_M115Regex = MultiRegex(collections.OrderedDict((
		("m115_xyz", re.compile("X: (?P<x>\d+) Y: (?P<y>\d+) Z: (?P<z>\d+)")),
		("m115_int", re.compile("(?P<key>Tool Count): (?P<value>\d+)")),
		("m115_string", re.compile("(?P<key>[^:]+): (?P<value>.*)")),
		("m115_unknown", re.compile(".*")),
	)))

	def __init__(self, conn, default_timeout = 1.0):
		self._conn = conn
		self._default_timeout = default_timeout
		self._rxbuf = ReceiveBuffer.create_for_socket(self._conn)

	@classmethod
	def connect_to_machine(cls, hostname, port = 8899, default_timeout = 1.0):
		conn = socket.create_connection((hostname, port), timeout = default_timeout)
		return cls(conn = conn, default_timeout = default_timeout)

	def tx_rx(self, cmd, timeout = None):
		if timeout is None:
			timeout = self._default_timeout
		print("-> %s" % (cmd))
		text_cmd = "~" + cmd + "\r\n"
		binary_cmd = text_cmd.encode("ascii")
		self._conn.send(binary_cmd)

		response_lines = [ ]
		while True:
			response_line = self._rxbuf.waitline(timeout = timeout).decode("utf-8")
			print("<- %s" % (response_line))
			if response_line == "ok":
				return response_lines
			response_lines.append(response_line)

	def tx_rx_binary(self, binary_cmd, timeout = None):
		print("-> %s" % (str(binary_cmd)))
		self._conn.send(binary_cmd)
		response_line = self._rxbuf.waitline(timeout = timeout).decode("utf-8")
		print("<- %s" % (response_line))
		return response_line

	def start_communication(self):
		response = self.tx_rx("M601 S1")
		if response != [ "CMD M601 Received.", "Control Success." ]:
			raise FlashForgeCommunicationException("Failed to take control of printer.")

	def end_communication(self):
		response = self.tx_rx("M602")
		if response != [ "CMD M602 Received.", "Control Release." ]:
			raise FlashForgeCommunicationException("Failed to release control of printer.")

	def set_led_color(self, r, g, b):
		assert(0 <= r <= 255)
		assert(0 <= g <= 255)
		assert(0 <= b <= 255)
		self.tx_rx("M146 r%d g%d b%d F0" % (r, g, b))

	def set_led_status(self, on_off):
		if on_off:
			self.set_led_color(255, 0, 0)
		else:
			self.set_led_color(0, 0, 0)

	def get_machine_information(self):
		class MachineInformationCallback():
			_KEY_MAP = {
				"Machine Type":		"machine_type",
				"Machine Name":		"machine_name",
				"Firmware":			"firmware",
				"SN":				"serial_number",
				"X":				"dimension_x",
				"Y":				"dimension_y",
				"Z":				"dimension_z",
				"Tool Count":		"tool_count",
				"Mac Address":		"mac_address",
			}

			def __init__(self):
				self._values = { }

			def _set(self, key, value):
				key = self._KEY_MAP.get(key, key)
				self._values[key] = value

			@property
			def values(self):
				return self._values

			def _match_m115_xyz(self, line, name, match):
				self._set("X", int(match["x"]))
				self._set("Y", int(match["y"]))
				self._set("Z", int(match["z"]))

			def _match_m115_string(self, line, name, match):
				self._set(match["key"], match["value"])

			def _match_m115_int(self, line, name, match):
				self._set(match["key"], int(match["value"]))

			def _match_m115_unknown(self, line, name, match):
				print("Warning: M115 command not understood: '%s'" % (line))

		mic = MachineInformationCallback()
		for line in self.tx_rx("M115")[1:]:
			line = line.rstrip("\r\n")
			self._M115Regex.fullmatch(line, mic, groupdict = True)

		return self._MachineInformation(**mic.values)

	def get_machine_status(self):
		print(self.tx_rx("M27"))
		print(self.tx_rx("M119"))
		self.tx_rx("M105")

	def move_home(self):
		self.tx_rx("G28")

	def send_file(self, filename, content):
		self.tx_rx("M28 %d 0:/user/%s" % (len(content), filename))
		chunk_size = 4096
		for chunk_index in range((len(content) + chunk_size - 1) // chunk_size):
			chunk_data = content[chunk_size * chunk_index : chunk_size * (chunk_index + 1)]
			chunk = GCodeChunk(chunk_index, chunk_data)
			self.tx_rx_binary(bytes(chunk))
		self.tx_rx("M29")

	def start_print_file(self, filename):
		self.tx_rx("M23 0:/user/%s" % (filename))

	def __enter__(self):
		self.start_communication()
		return self

	def __exit__(self, *args):
		self.end_communication()
		self.close()

	def close(self):
		pass
