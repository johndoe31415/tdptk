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

import re
import enum
import collections
from .Exceptions import MalformedGcodeException

class GCodeCommandArguments():
	def __init__(self, arg_string):
		self._arg_string = arg_string
		self._dict = None
		self._float_dict = None

	def arg_str(self):
		return self._arg_string

	@property
	def as_dict(self):
		if self._dict is None:
			self._dict = { }
			for item in self._arg_string.split():
				key = item[0]
				value = item[1:]
				self._dict[key] = value
		return self._dict

	@property
	def float_dict(self):
		if self._float_dict is None:
			self._float_dict = { key: float(value) for (key, value) in self.as_dict.items() }
		return self._float_dict

	def get(self, key, default_value = None):
		return self.as_dict.get(key, default_value)

	def __getitem__(self, key):
		return self.as_dict[key]

class GCodeHook():
	def __init__(self, interpreter = None):
		self._interpreter = interpreter

	def claim(self, interpreter):
		self._interpreter = interpreter

	def extrude(self, tool, old_pos, new_pos, extruded_length):
		pass

	def movement(self, old_pos, new_pos):
		pass

	def tool_change(self, tool):
		pass

	def bed_temperature(self, temp_degc):
		pass

	def nozzle_temperature(self, tool, temp_degc):
		pass

	def comment(self, comment):
		pass

class GCodeBaseInterpreter():
	def __init__(self, hooks = None):
		self._pos = { }
		self._pos_absolute = False
		self._tool = 0
		if hooks is None:
			self._hooks = [ ]
		else:
			self._hooks = hooks
			for hook in self._hooks:
				hook.claim(self)

	def add_hook(self, hook):
		hook.claim(self)
		self._hooks.append(hook)

	@property
	def pos(self):
		if self.tool not in self._pos:
			self._pos[self.tool] = { "X": 0, "Y": 0, "Z": 0, "E": 0, "F": 0 }
		return self._pos[self.tool]

	@pos.setter
	def pos(self, value):
		self._pos[self.tool] = value

	@property
	def tool(self):
		return self._tool

	def _fire_hooks(self, hook_name, *args):
		for hook in self._hooks:
			method = getattr(hook, hook_name)
			method(*args)

	def _movement(self, old_pos, new_pos):
		extruded_length = new_pos["E"] - old_pos["E"]
		self._fire_hooks("movement", old_pos, new_pos)
		if extruded_length > 0:
			self._fire_hooks("extrude", self.tool, old_pos, new_pos, extruded_length)

	def comment(self, comment_text):
		self._fire_hooks("comment", comment_text)

	def command(self, command_text, command_arg):
		if command_text in [ "G0", "G1" ]:
			new_pos = dict(self.pos)
			for (axis, pos) in command_arg.float_dict.items():
				if self._pos_absolute:
					new_pos[axis] = pos
				else:
					new_pos[axis] += pos
			self._movement(self.pos, new_pos)
			self.pos = new_pos
		elif command_text == "G90":
			self._pos_absolute = True
		elif command_text == "G91":
			self._pos_absolute = False
		elif command_text == "G92":
			# Set position
			for (axis, pos) in command_arg.float_dict.items():
				self.pos[axis] = pos
		elif command_text == "M108":
			# Set tool (left or right extruder)
			self._tool = int(command_arg["T"])
			self._fire_hooks("tool_change", self._tool)
		elif command_text == "M104":
			# Set nozzle temperature
			tool = int(command_arg.get("T", 0))
			temperature = float(command_arg["S"])
			self._fire_hooks("nozzle_temperature", tool, temperature)
		elif command_text == "M140":
			# Set bed temperature
			temperature = float(command_arg["S"])
			self._fire_hooks("bed_temperature", temperature)

class GCodeParser():
	_GCODE_RE = re.compile(r"\s*((?P<cmd_code>[A-Z]\d+)(\s+(?P<cmd_args>[^;]+))?)?(\s*;(?P<comment>.*))?")

	def __init__(self, interpreter):
		self._interpreter = interpreter

	def parse(self, cmd):
		match = self._GCODE_RE.fullmatch(cmd)
		if match is None:
			raise MalformedGcodeException("Do not understand G-code: '%s'" % (cmd))
		match = match.groupdict()
		if match["cmd_code"] is not None:
			if match["cmd_args"] is None:
				args = None
			else:
				args = GCodeCommandArguments(match["cmd_args"])
			self._interpreter.command(match["cmd_code"], args)
		if match["comment"] is not None:
			self._interpreter.comment(match["comment"])

	def parse_all(self, gcode):
		for line in gcode.split("\n"):
			self.parse(line)

class PrintingRegion(enum.Enum):
	Shell = "shell"
	Infill = "infill"
	Raft = "raft"
	Support = "support"
	Unknown = "unknown"

class GCodeInformationHook(GCodeHook):
	def __init__(self):
		super().__init__(self)
		self._bed_maxtemp = 0
		self._tool_maxtemp = collections.defaultdict(float)
		self._total_extruded_length = collections.defaultdict(float)
		self._movement_command_count = 0
		self._region = None
		self._min_z_change = 1

	def comment(self, comment_text):
		if comment_text in [ "shell", "infill", "raft" ]:
			self._region = PrintingRegion(comment_text)
		elif comment_text == "support-start":
			self._region = PrintingRegion.Support
		elif comment_text == "support-end":
			self._region = None
		elif comment_text.startswith("TYPE:"):
			support_type = comment_text[5:]
			self._region = {
				"FILL":			PrintingRegion.Infill,
				"SKIN":			PrintingRegion.Shell,
				"WALL-INNER":	PrintingRegion.Infill,
				"WALL-OUTER":	PrintingRegion.Shell,
				"SUPPORT":		PrintingRegion.Support,
			}.get(support_type, PrintingRegion.Unknown)

	@property
	def region(self):
		return self._region

	@property
	def total_extruded_length(self):
		return self._total_extruded_length

	@property
	def bed_max_temp(self):
		return self._bed_maxtemp

	@property
	def tool_max_temp(self):
		return self._tool_maxtemp

	@property
	def min_z_change(self):
		return self._min_z_change

	def bed_temperature(self, temp_degc):
		self._bed_maxtemp = max(self._bed_maxtemp, temp_degc)

	def nozzle_temperature(self, tool, temp_degc):
		self._tool_maxtemp[tool] = max(self._tool_maxtemp[tool], temp_degc)

	def movement(self, old_pos, new_pos):
		self._movement_command_count += 1
		z_change = new_pos["Z"] - old_pos["Z"]
		if 0 < z_change < 1:
			self._min_z_change = min(self._min_z_change, z_change)

	def extrude(self, tool, old_pos, new_pos, extruded_length):
		self._total_extruded_length[tool] += extruded_length

class GCodePOVRayHook(GCodeHook):
	def __init__(self, povray_renderer, info_hook):
		super().__init__(self)
		self._renderer = povray_renderer
		self._info_hook = info_hook
		self._stats = {
			"extrude_commands":		0,
			"wrong_region":			0,
		}

	@property
	def stats(self):
		return self._stats

	def extrude(self, tool, old_pos, new_pos, extruded_length):
		self._stats["extrude_commands"] += 1

		if self._info_hook.region not in [ PrintingRegion.Shell, PrintingRegion.Infill ]:
			self._stats["wrong_region"] += 1
			return

		self._renderer.add_cylinder(old_pos, new_pos)
