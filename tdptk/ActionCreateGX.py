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
import tempfile
import subprocess
from .BaseAction import BaseAction
from .XGCodeFile import XGCodeFile, XGCodeFlags
from .GCodeInterpreter import GCodeBaseInterpreter, GCodeParser
from .POVRayInterpreter import POVRayInterpreter, POVRayStyle

class ActionCreateGX(BaseAction):
	def run(self):
		if not self._args.force:
			if os.path.exists(self._args.gx_filename):
				print("Refusing to overwrite: %s" % (self._args.gx_filename))
				sys.exit(1)

		with open(self._args.gcode_filename) as f:
			gcode_data = f.read()

		# Parse G-code to gather metadata about file
		interpreter = GCodeBaseInterpreter()
		parser = GCodeParser(interpreter)
		parser.parse_all(gcode_data)

		# Render the G-code using POV-ray so we have a preview bitmap
		povray_interpreter = POVRayInterpreter(width = 80, height = 60, oversample_factor = 4, style = POVRayStyle.BlackWhite, verbosity = self._args.verbose)
		parser = GCodeParser(povray_interpreter)
		parser.parse_all(gcode_data)
		with tempfile.NamedTemporaryFile(suffix = ".png") as png_outfile, tempfile.NamedTemporaryFile(suffix = ".bmp") as bmp_outfile:
			povray_interpreter.render_image(png_outfile.name, trim_image = True)
			subprocess.check_call([ "convert", "-colorspace", "RGB", png_outfile.name, bmp_outfile.name ])
			bitmap_data = bmp_outfile.read()

		flags = 0
		if interpreter.total_extruded_length.get(0, 0) > 0:
			flags |= XGCodeFlags.Use_Right_Extruder
		if interpreter.total_extruded_length.get(1, 0) > 0:
			flags |= XGCodeFlags.Use_Left_Extruder

		header_dict = {
			"print_flags":					flags,
			"print_time_secs":				60,			# TODO FIXME
			"print_speed_mm_per_sec":		60,			# TODO FIXME
			"layer_height_microns":			180,		# TODO FIXME
			"perimeter_shell_count":		0,
			"platform_temp_deg_c":			round(interpreter.bed_max_temp),

			"extruder_temp_right_deg_c":	round(interpreter.tool_max_temp.get(0, 0)),
			"filament_use_mm_right":		round(interpreter.total_extruded_length.get(0, 0)),
			"material_right":				self._args.material_right,

			"extruder_temp_left_deg_c":		round(interpreter.tool_max_temp.get(1, 0)),
			"filament_use_mm_left":			round(interpreter.total_extruded_length.get(1, 0)),
			"material_left":				self._args.material_left,
		}
		xgcode = XGCodeFile.from_header_dict(header_dict = header_dict, bitmap_data = bitmap_data, gcode_data = gcode_data.encode())
		xgcode.write(self._args.gx_filename)
