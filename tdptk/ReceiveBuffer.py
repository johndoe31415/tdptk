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
import socket
import threading
import select

class ReceiveBufferException(Exception): pass
class ReceiveBufferTimeout(ReceiveBufferException): pass
class ReceiveBufferClosed(ReceiveBufferException): pass

class ReceiveBuffer():
	def __init__(self, nonblocking_read_callback, block_until_readable_bytes_callback, default_timeout = 1.0, line_splitter = b"\r\n"):
		self._nonblocking_read_callback = nonblocking_read_callback
		self._block_until_readable_bytes_callback = block_until_readable_bytes_callback
		self._line_splitter = line_splitter
		self._rx_buffer = bytearray()
		self._default_timeout = default_timeout
		self._closed = False

	@classmethod
	def create_for_socket(cls, conn, read_chunk_size = 4096, **kwargs):
		nonblocking_read_callback = lambda: conn.recv(read_chunk_size)
		def block_until_readable_bytes_callback(length, abs_timeout):
			timeout = abs_timeout - time.time()
			if timeout <= 0:
				# Time already passed
				return False
			(rsock, wsock, esock) = select.select([ conn ],  [ ], [ ], timeout)
			return len(rsock) != 0

		kwargs.update({
			"nonblocking_read_callback": nonblocking_read_callback,
			"block_until_readable_bytes_callback": block_until_readable_bytes_callback,
		})
		return cls(**kwargs)

	def _wait_for_condition(self, splitter_condition, wait_for_bytes, timeout = None):
		if self._closed:
			raise ReceiveBufferClosed("Peer closed connection.")

		if timeout is None:
			timeout = self._default_timeout
		abs_timeout = time.time() + timeout

		while (not self._closed) and (time.time() < abs_timeout):
			split_line = splitter_condition(self._rx_buffer)
			if len(split_line) == 2:
				(result, self._rx_buffer) = split_line
				return result

			remaining_bytes = wait_for_bytes(self._rx_buffer)
			if self._block_until_readable_bytes_callback(remaining_bytes, abs_timeout):
				new_data = self._nonblocking_read_callback()
				if len(new_data) == 0:
					# Remote closed connection.
					self._closed = True
					raise ReceiveBufferClosed("Peer closed connection.")
				self._rx_buffer += new_data

		# Timeout
		raise ReceiveBufferTimeout("Timeout after %.3f secs" % (timeout))

	def waitbytes(self, length, timeout = None):
		def splitter_condition(rx_buffer):
			if len(rx_buffer) < length:
				return (rx_buffer, )
			else:
				return (rx_buffer[:length], rx_buffer[length:])
		def wait_for_bytes(rx_buffer):
			return length - len(rx_buffer)
		return self._wait_for_condition(splitter_condition = splitter_condition, wait_for_bytes = wait_for_bytes, timeout = timeout)

	def waitline(self, timeout = None):
		def splitter_condition(rx_buffer):
			return rx_buffer.split(self._line_splitter, maxsplit = 1)
		def wait_for_bytes(rx_buffer):
			return len(self._line_splitter)
		return self._wait_for_condition(splitter_condition = splitter_condition, wait_for_bytes = wait_for_bytes, timeout = timeout)


if __name__ == "__main__":
	(host, port) = ("127.0.0.1", 9999)
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind((host, port))
		sock.listen(1)
		print("Connect by: socat - TCP4:%s:%d" % (host, port))
		print("Connect by: telnet %s %d" % (host, port))
		(conn, addr) = sock.accept()
		print("Client connected.")
		with conn:
			reader_thread = ReceiveBuffer.create_for_socket(conn)
			while True:
				try:
					line = reader_thread.waitline()
					#line = reader_thread.waitbytes(5)
					print("Got line: %s" % (str(line)))
					if line == b"q":
						conn.shutdown(socket.SHUT_RDWR)
				except ReceiveBufferTimeout as e:
					print("Timeout: %s" % (str(e)))
