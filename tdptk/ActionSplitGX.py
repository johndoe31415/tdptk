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

class ActionSplitGX(BaseAction):
	def run(self):
		if not self._args.force:
			if os.path.exists(self._args.json_metadata_filename):
				print("Refusing to overwrite: %s" % (self._args.json_metadata_filename))
				sys.exit(1)
			if os.path.exists(self._args.preview_bmp_filename):
				print("Refusing to overwrite: %s" % (self._args.preview_bmp_filename))
				sys.exit(1)
			if os.path.exists(self._args.gcode_filename):
				print("Refusing to overwrite: %s" % (self._args.gcode_filename))
				sys.exit(1)
		xgcode = XGCodeFile.read(self._args.gx_filename)
		with open(self._args.json_metadata_filename, "w") as f:
			json.dump(xgcode.header_dict, f, indent = 4)
			f.write("\n")
		with open(self._args.preview_bmp_filename, "wb") as f:
			f.write(xgcode.bitmap_data)
		with open(self._args.gcode_filename, "wb") as f:
			f.write(xgcode.gcode_data)
