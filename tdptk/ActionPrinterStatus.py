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

class ActionPrinterStatus(BaseAction):
	def _run_uri(self, uri_str):
		uri = PrinterURI.parse(uri_str)
		if uri.protocol == PrinterProtocol.FlashForge:
			with FlashForgeProtocol.connect_to_machine(uri.host, port = uri.port) as conn:
				print(conn.get_machine_information())
				print(conn.get_machine_status())

	def run(self):
		for uri_str in self._args.uri:
			print("%s" % (uri_str))
			self._run_uri(uri_str)
			print()
