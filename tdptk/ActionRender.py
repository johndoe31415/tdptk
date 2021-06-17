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
from .GCodeInterpreter import GCodeBaseInterpreter, GCodeParser, GCodePOVRayHook
from .POVRayRenderer import POVRayRenderer, POVRayStyle
from .STLFile import STLFile

class ActionRender(BaseAction):
	def run(self):
		if not self._args.force:
			if os.path.exists(self._args.output_filename):
				print("Refusing to overwrite: %s" % (self._args.output_filename))
				sys.exit(1)

		if self._args.filetype == "auto":
			filetype = os.path.splitext(self._args.input_filename)[1][1:]
		else:
			filetype = self._args.filetype

		if filetype == "gx":
			xgcode = XGCodeFile.read(self._args.input_filename)
			gcode_data = xgcode.gcode_data.decode("ascii")
		elif filetype == "g":
			with open(self._args.input_filename) as f:
				gcode_data = f.read()
		elif filetype == "stl":
			stl = STLFile.read(self._args.input_filename)
		else:
			raise NotImplementedError("Unknown input file type: %s" % (filetype))

		povray_renderer = POVRayRenderer(width = self._args.dimensions[0], height = self._args.dimensions[1], oversample_factor = self._args.oversample, style = POVRayStyle(self._args.style), verbosity = self._args.verbose)
		if filetype in [ "gx", "g" ]:
			parser = GCodeParser(GCodeBaseInterpreter(hooks = [ GCodePOVRayHook(povray_renderer) ]))
			parser.parse_all(gcode_data)
		elif filetype == "stl":
			for triangle in stl:
				povray_renderer.add_triangle((triangle.vertex1_x, triangle.vertex1_y, triangle.vertex1_z), (triangle.vertex2_x, triangle.vertex2_y, triangle.vertex2_z), (triangle.vertex3_x, triangle.vertex3_y, triangle.vertex3_z))
		else:
			raise NotImplementedError("Unknown input file type: %s" % (filetype))

		if self._args.output_filename.endswith(".pov"):
			with open(self._args.output_filename, "w") as f:
				f.write(povray_renderer.render_source())
		else:
			povray_renderer.render_image(self._args.output_filename, additional_povray_options = self._args.povray, show_image = self._args.show, trim_image = not self._args.no_trim)
