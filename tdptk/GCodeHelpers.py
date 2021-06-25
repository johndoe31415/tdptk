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

from .GCodeInterpreter import GCodeBaseInterpreter, GCodeParser, GCodeSpeedHook

class GCodeHelpers():
	@classmethod
	def estimate_gcode_timing(cls, gcode, model_parameters):
		speed = GCodeSpeedHook(model_parameters = model_parameters, log_execution_time = True)
		interpreter = GCodeBaseInterpreter(hooks = [ speed ])
		parser = GCodeParser(interpreter)
		parser.parse_all(gcode)

		data = {
			"x":	[ ],
			"y":	[ ],
		}
		for (x, y) in speed.execution_times:
			data["x"].append(x)
			data["y"].append(y)
		return data
