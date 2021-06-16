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

class GCodeBaseInterpreter():
	def __init__(self):
		self._pos = { }
		self._pos_absolute = False
		self._total_extruded_length = collections.defaultdict(float)
		self._movement_command_count = 0
		self._area = None
		self._tool = 0
		self._bed_maxtemp = 0
		self._tool_maxtemp = collections.defaultdict(float)

	@property
	def pos(self):
		if self.tool not in self._pos:
			self._pos[self.tool] = { "X": 0, "Y": 0, "Z": 0, "E": 0, "F": 0 }
		return self._pos[self.tool]

	@pos.setter
	def pos(self, value):
		self._pos[self.tool] = value

	@property
	def area(self):
		return self._area

	@property
	def tool(self):
		return self._tool

	@property
	def total_extruded_length(self):
		return self._total_extruded_length

	@property
	def bed_max_temp(self):
		return self._bed_maxtemp

	@property
	def tool_max_temp(self):
		return self._tool_maxtemp

	def comment(self, comment_text):
		if comment_text in [ "shell", "infill", "raft" ]:
			self._area = comment_text
		elif comment_text == "support-start":
			self._area = "support"
		elif comment_text == "support-end":
			self._area = None
		elif comment_text.startswith("TYPE:"):
			support_type = comment_text[5:]
			self._area = {
				"FILL":			"infill",
				"SKIN":			"shell",
				"WALL-INNER":	"infill",
				"WALL-OUTER":	"shell",
				"SUPPORT":		"support",
			}.get(support_type, support_type)

	def _extrude(self, tool, old_pos, new_pos):
		pass

	def _movement(self, old_pos, new_pos):
		extruded_length = new_pos["E"] - old_pos["E"]
		self._total_extruded_length[self.tool] += extruded_length
		if extruded_length > 0:
			self._extrude(self.tool, old_pos, new_pos)
		self._movement_command_count += 1

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
		elif command_text == "M104":
			# Set nozzle temperature
			tool = int(command_arg.get("T", 0))
			self._tool_maxtemp[tool] = max(self._tool_maxtemp[tool], float(command_arg["S"]))
		elif command_text == "M140":
			# Set bed temperature
			self._bed_maxtemp = max(self._bed_maxtemp, float(command_arg["S"]))

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
