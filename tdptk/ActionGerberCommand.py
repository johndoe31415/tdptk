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

from .BaseAction import BaseAction
from .FlashForgeProtocol import FlashForgeProtocol
from .PrinterURI import PrinterProtocol, PrinterURI

class ActionGerberCommand(BaseAction):
	def _run_command(self, command):
		uri = PrinterURI.parse(self._args.uri)
		if uri.protocol == PrinterProtocol.FlashForge:
			with FlashForgeProtocol.connect_to_machine(uri.host, port = uri.port, default_timeout = self._args.timeout) as conn:
				print(conn.tx_rx(command))

	def run(self):
		for command in self._args.commands:
			self._run_command(command)
