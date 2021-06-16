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

import os
from .BaseAction import BaseAction
from .PrinterURI import PrinterURI, PrinterProtocol
from .FlashForgeProtocol import FlashForgeProtocol

class ActionPrint(BaseAction):
	def run(self):
		with open(self._args.input_filename, "rb") as f:
			data_file_content = f.read()
		filename = os.path.basename(self._args.input_filename)

		uri = PrinterURI.parse(self._args.printer_uri)
		if uri.protocol == PrinterProtocol.FlashForge:
			with FlashForgeProtocol.connect_to_machine(uri.host, port = uri.port) as conn:
				conn.send_file(filename, data_file_content)
				conn.start_print_file(filename)
		else:
			raise NotImplementedError("Printing not implemented on '%s' protocol printer." % (uri.protocol.name))
