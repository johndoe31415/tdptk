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
import sys
import json
from .BaseAction import BaseAction
from .XGCodeFile import XGCodeFile

class ActionMergeGX(BaseAction):
	def run(self):
		if not self._args.force:
			if os.path.exists(self._args.gx_filename):
				print("Refusing to overwrite: %s" % (self._args.gx_filename))
				sys.exit(1)

		with open(self._args.json_metadata_filename) as f:
			header_dict = json.load(f)
		with open(self._args.preview_bmp_filename, "rb") as f:
			bitmap_data = f.read()
		with open(self._args.gcode_filename, "rb") as f:
			gcode_data = f.read()

		xgcode = XGCodeFile.from_header_dict(header_dict = header_dict, bitmap_data = bitmap_data, gcode_data = gcode_data)
		xgcode.write(self._args.gx_filename)
