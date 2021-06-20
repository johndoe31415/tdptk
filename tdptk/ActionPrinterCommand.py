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
import json
from .BaseAction import BaseAction
from .FlashForgeProtocol import FlashForgeProtocol
from .PrinterURI import PrinterProtocol, PrinterURI

class ActionPrinterCommand(BaseAction):
	def _run_command(self, command):
		if command == "cancel":
			self._conn.cancel_print()
		elif command == "pause":
			self._conn.pause_print()
		elif command == "resume":
			self._conn.resume_print()
		elif command == "info":
			print(self._conn.get_machine_status())
		elif command == "monitor":
			while True:
				progress = self._conn.get_machine_progress()
				print("Progress: %.1f%%" % (progress.progress / progress.total * 100))
				time.sleep(5)
		elif command == "benchmark":
			t0 = time.time()
			while True:
				pos = self._conn.get_current_position()
				t = time.time()
				trel = t - t0
				data = { "t": t, "trel": trel, "A": pos["A"] }
				print("%.3f: %.3f" % (trel, pos["A"]))
				with open("benchmark.txt", "a") as f:
					print(json.dumps(data), file = f)
				time.sleep(1)
		else:
			raise NotImplementedError("Not implemented: %s" % (command))

	def _run_commands(self, commands):
		for command in commands:
			self._run_command(command)

	def run(self):
		uri = PrinterURI.parse(self._args.uri)
		if uri.protocol == PrinterProtocol.FlashForge:
			with FlashForgeProtocol.connect_to_machine(uri.host, port = uri.port, default_timeout = self._args.timeout) as conn:
				self._conn = conn
				self._run_commands(self._args.commands)
