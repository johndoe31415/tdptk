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
from .Exceptions import CannotDetermineFiletypeException
from .XGCodeFile import XGCodeFile, XGCodeFlags
from .GCodeInterpreter import GCodeBaseInterpreter, GCodeParser, GCodeInformationHook, GCodeSpeedHook

class ActionFileInfo(BaseAction):
	_EXTENSIONS = {
		".gx":		"gx",
		".g":		"g",
	}

	def _run_file_gx(self, filename):
		xgcode = XGCodeFile.read(filename)
		info = GCodeInformationHook()
		speed = GCodeSpeedHook()
		interpreter = GCodeBaseInterpreter(hooks = [ info, speed ])
		parser = GCodeParser(interpreter)
		parser.parse_all(xgcode.gcode_data.decode("ascii"))

		print("Preview image   : %d bytes bitmap" % (len(xgcode.bitmap_data)))
		print("G-code          : %d bytes machine data" % (len(xgcode.gcode_data)))
		print("Flags           : %s" % (", ".join(flag.name for flag in xgcode.flags)))
		print("Layer height    : %d microns (%d microns according to G-code)" % (xgcode.header.layer_height_microns, round(info.median_z_change * 1000)))
		print("Perimeter shells: %d" % (xgcode.header.perimeter_shell_count))
		hrs = xgcode.header.print_time_secs // 3600
		mins = xgcode.header.print_time_secs % 3600 // 60
		secs = xgcode.header.print_time_secs % 3600 % 60
		print("Print time      : %d:%02d:%02d h:m:s (estimated %s h:m:s from G-code)" % (hrs, mins, secs, speed.print_time_hms))
		print("Print speed     : %d mm/sec (%d mm/sec from G-code)" % (xgcode.header.print_speed_mm_per_sec, round(speed.max_feedrate_mm_per_sec)))
		print("Bed temperature : %d°C (max %d°C according to G-code)" % (xgcode.header.platform_temp_deg_c, info.bed_max_temp))
		if (self._args.verbose >= 2) or (XGCodeFlags.Use_Right_Extruder in xgcode.flags):
			print()
			print("Right Extruder:")
			print("   Material    : %s" % (xgcode.material_right.name))
			print("   Filament use: %.2fm (%.2fm according to G-code)" % (xgcode.header.filament_use_mm_right / 1000, info.total_extruded_length[0] / 1000))
			print("   Temperature : %d°C (max %d°C according to G-code)" % (xgcode.header.extruder_temp_right_deg_c, info.tool_max_temp[0]))
		if (self._args.verbose >= 2) or (XGCodeFlags.Use_Left_Extruder in xgcode.flags):
			print()
			print("Left Extruder:")
			print("   Material    : %s" % (xgcode.material_left.name))
			print("   Filament use: %.2fm (%.2fm according to G-code)" % (xgcode.header.filament_use_mm_left / 1000, info.total_extruded_length[1] / 1000))
			print("   Temperature : %d°C (max %d°C according to G-code)" % (xgcode.header.extruder_temp_left_deg_c, info.tool_max_temp[1]))

	def _run_file_g(self, filename):
		info = GCodeInformationHook()
		speed = GCodeSpeedHook()
		interpreter = GCodeBaseInterpreter(hooks = [ info, speed ])
		parser = GCodeParser(interpreter)
		with open(filename) as f:
			parser.parse_all(f.read())
		print("Bed temperature : %d°C" % (info.bed_max_temp))
		print("Print time      : %s h:m:s" % (speed.print_time_hms))
		print("Print speed     : %d mm/sec" % (round(speed.max_feedrate_mm_per_sec)))
		for (tool, length) in sorted(info.total_extruded_length.items()):
			print()
			print("Extruder #%d" % (tool + 1))
			print("   Filament use: %.2fm" % (info.total_extruded_length[tool] / 1000))
			print("   Temperature : %d°C" % (info.tool_max_temp[tool]))

	def _run_file(self, filename):
		if self._args.filetype == "auto":
			(base, ext) = os.path.splitext(filename)
			ext = ext.lower()
			if ext not in self._EXTENSIONS:
				raise CannotDetermineFiletypeException("Do not know what type of file '%s' extension is." % (ext))

			filetype = self._EXTENSIONS[ext]
		else:
			filetype = self._args.filetype

		method_name = "_run_file_%s" % (filetype)
		method = getattr(self, method_name)
		method(filename)

	def run(self):
		for filename in self._args.filename:
			print(filename)
			self._run_file(filename)
			print()
