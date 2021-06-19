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
from .GCodeInterpreter import GCodeBaseInterpreter, GCodeParser, GCodeInformationHook, GCodePOVRayHook, GCodeSpeedHook
from .POVRayRenderer import POVRayRenderer, POVRayStyle

class ActionCreateGX(BaseAction):
	def run(self):
		if not self._args.force:
			if os.path.exists(self._args.gx_filename):
				print("Refusing to overwrite: %s" % (self._args.gx_filename))
				sys.exit(1)

		with open(self._args.gcode_filename) as f:
			gcode_data = f.read()

		# Render the G-code using POV-Ray so we have a preview bitmap
		povray_renderer = POVRayRenderer(width = 80, height = 60, oversample_factor = 4, style = POVRayStyle.BlackWhite, verbosity = self._args.verbose)

		# Parse G-code to gather metadata about file and fill the POV-Ray renderer with data
		interpreter = GCodeBaseInterpreter()
		info = GCodeInformationHook()
		speed = GCodeSpeedHook()
		interpreter.add_hook(info)
		interpreter.add_hook(speed)
		interpreter.add_hook(GCodePOVRayHook(povray_renderer, info))
		parser = GCodeParser(interpreter)
		parser.parse_all(gcode_data)

		with tempfile.NamedTemporaryFile(suffix = ".png") as png_outfile, tempfile.NamedTemporaryFile(suffix = ".bmp") as bmp_outfile:
			povray_renderer.render_image(png_outfile.name, trim_image = True)
			subprocess.check_call([ "convert", "-colorspace", "RGB", png_outfile.name, bmp_outfile.name ])
			bitmap_data = bmp_outfile.read()

		flags = 0
		if info.total_extruded_length.get(0, 0) > 0:
			flags |= XGCodeFlags.Use_Right_Extruder
		if info.total_extruded_length.get(1, 0) > 0:
			flags |= XGCodeFlags.Use_Left_Extruder

		header_dict = {
			"print_flags":					flags,
			"print_time_secs":				round(speed.print_time_secs),
			"print_speed_mm_per_sec":		round(speed.max_feedrate_mm_per_sec),
			"layer_height_microns":			round(info.median_z_change * 1000),
			"perimeter_shell_count":		0,
			"platform_temp_deg_c":			round(info.bed_max_temp),

			"extruder_temp_right_deg_c":	round(info.tool_max_temp.get(0, 0)),
			"filament_use_mm_right":		round(info.total_extruded_length.get(0, 0)),
			"material_right":				self._args.material_right,

			"extruder_temp_left_deg_c":		round(info.tool_max_temp.get(1, 0)),
			"filament_use_mm_left":			round(info.total_extruded_length.get(1, 0)),
			"material_left":				self._args.material_left,
		}
		xgcode = XGCodeFile.from_header_dict(header_dict = header_dict, bitmap_data = bitmap_data, gcode_data = gcode_data.encode())
		xgcode.write(self._args.gx_filename)
