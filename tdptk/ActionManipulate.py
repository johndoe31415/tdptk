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
from .BaseAction import BaseAction
from .GCodeInterpreter import GCodeBaseInterpreter, GCodeParser, GCodeSpeedHook, GCodeManipulationRemoveExtrusionHook, GCodeManipulationInsertProgressHook

class ActionManipulate(BaseAction):
	def _run_remove_extrusion(self):
		hook = GCodeManipulationRemoveExtrusionHook()
		GCodeParser(GCodeBaseInterpreter(hooks = [ hook ])).parse_all(self._gcode_data)
		self._gcode_data = hook.serialize()

	def _run_insert_progress_comment(self):
		# First determine how long we need in total
		speed_hook = GCodeSpeedHook()
		GCodeParser(GCodeBaseInterpreter(hooks = [ speed_hook ])).parse_all(self._gcode_data)

		# Then run again with the required information
		total_printing_time = speed_hook.print_time_secs
		speed_hook = GCodeSpeedHook()
		hook = GCodeManipulationInsertProgressHook(speed_hook = speed_hook, total_printing_time = total_printing_time)
		GCodeParser(GCodeBaseInterpreter(hooks = [ speed_hook, hook ])).parse_all(self._gcode_data)
		self._gcode_data = hook.serialize()

	def run(self):
		if not self._args.force:
			if os.path.exists(self._args.output_filename):
				print("Refusing to overwrite: %s" % (self._args.output_filename))
				sys.exit(1)

		with open(self._args.input_filename) as f:
			self._gcode_data = f.read()

		if self._args.remove_extrusion:
			self._run_remove_extrusion()
		if self._args.insert_progress_comment:
			self._run_insert_progress_comment()

		with open(self._args.output_filename, "w") as f:
			f.write(self._gcode_data)
