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
import math
import collections
import numpy
from .Exceptions import MalformedGcodeException

class GCodes(enum.Enum):
	RapidMovement = "G0"
	ControlledMovement = "G1"
	UseAbsolutePositioning = "G90"
	UseRelativePositioning = "G91"
	SetPositionToValue = "G92"
	Dwell = "G4"
	MoveHomePosition = "G28"

	GetCurrentPosition = "M114"
	SetActiveExtruder = "M108"
	SetExtruderNozzleTemperature = "M104"
	SetBedTemperature = "M140"
	EmergencyStop = "M112"

class GCodeCommand():
	def __init__(self, cmd_string, arg_string, comment = None, gcode_class = GCodes):
		try:
			self._cmd = gcode_class(cmd_string)
		except ValueError:
			self._cmd = None
		self._cmd_string = cmd_string
		self._arg_string = arg_string
		self._comment = comment
		self._dict = self._parse_args(self._arg_string)

	@property
	def have_command(self):
		return self._cmd_string is not None

	@property
	def have_args(self):
		return self._arg_string is not None

	@property
	def have_comment(self):
		return self._comment is not None

	@property
	def cmd(self):
		return self._cmd

	@property
	def cmd_str(self):
		return self._cmd_string

	@property
	def arg_str(self):
		return self._arg_string

	@property
	def arg_count(self):
		return len(self._dict)

	@property
	def comment(self):
		return self._comment

	@staticmethod
	def _parse_args(arg_string):
		arg_dict = collections.OrderedDict()
		if arg_string is not None:
			for item in arg_string.split():
				key = item[0]
				value = item[1:]
				arg_dict[key] = value
		return arg_dict

	@property
	def float_dict(self):
		return { key: float(value) for (key, value) in self._dict.items() }

	def get(self, key, default_value = None):
		return self._dict.get(key, default_value)

	def has_arg(self, key):
		return key in self._dict

	def remove_arg(self, key):
		del self._dict[key]

	def __getitem__(self, key):
		return self._dict[key]

	def __setitem__(self, key, value):
		self._dict[key] = value

	def __str__(self):
		text = ""
		if self.have_command:
			text += self._cmd_string
			if self.have_args:
				text += " " + (" ".join("%s%s" % (key, value) for (key, value) in self._dict.items()))
		if self.have_comment:
			if text != "":
				text += " "
			text += ";%s" % (self._comment)
		return text

class GCodeHook():
	def __init__(self, interpreter = None):
		self._interpreter = interpreter

	def claim(self, interpreter):
		self._interpreter = interpreter

	def extrude(self, tool, old_pos, new_pos, extruded_length, max_feedrate):
		pass

	def movement(self, old_pos, new_pos, max_feedrate):
		pass

	def tool_change(self, tool):
		pass

	def bed_temperature(self, temp_degc):
		pass

	def nozzle_temperature(self, tool, temp_degc):
		pass

	def command(self, command):
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
		max_feedrate = new_pos["F"]
		self._fire_hooks("movement", old_pos, new_pos, max_feedrate)
		if extruded_length > 0:
			self._fire_hooks("extrude", self.tool, old_pos, new_pos, extruded_length, max_feedrate)

	def command(self, command):
		self._fire_hooks("command", command)
		if command.cmd in [ GCodes.RapidMovement, GCodes.ControlledMovement ]:
			new_pos = dict(self.pos)
			for (axis, pos) in command.float_dict.items():
				if self._pos_absolute:
					new_pos[axis] = pos
				else:
					new_pos[axis] += pos
			self._movement(self.pos, new_pos)
			self.pos = new_pos
		elif command.cmd == GCodes.UseAbsolutePositioning:
			self._pos_absolute = True
		elif command.cmd == GCodes.UseRelativePositioning:
			self._pos_absolute = False
		elif command.cmd == GCodes.SetPositionToValue:
			# Set position
			for (axis, pos) in command.float_dict.items():
				self.pos[axis] = pos
		elif command.cmd == GCodes.SetActiveExtruder:
			self._tool = int(command["T"])
			self._fire_hooks("tool_change", self._tool)
		elif command.cmd == GCodes.SetExtruderNozzleTemperature:
			tool = int(command.get("T", 0))
			temperature = float(command["S"])
			self._fire_hooks("nozzle_temperature", tool, temperature)
		elif command.cmd == GCodes.SetBedTemperature:
			temperature = float(command["S"])
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
		cmd = GCodeCommand(match["cmd_code"], match["cmd_args"], match["comment"])
		self._interpreter.command(cmd)

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
		self._z_changes = [ ]

	def command(self, command):
		if command.comment is None:
			return

		if command.comment in [ "shell", "infill", "raft" ]:
			self._region = PrintingRegion(command.comment)
		elif command.comment == "support-start":
			self._region = PrintingRegion.Support
		elif command.comment == "support-end":
			self._region = None
		elif command.comment.startswith("TYPE:"):
			support_type = command.comment[5:]
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
	def median_z_change(self):
		if len(self._z_changes) == 0:
			return 0
		else:
			return float(numpy.median(self._z_changes))

	def bed_temperature(self, temp_degc):
		self._bed_maxtemp = max(self._bed_maxtemp, temp_degc)

	def nozzle_temperature(self, tool, temp_degc):
		self._tool_maxtemp[tool] = max(self._tool_maxtemp[tool], temp_degc)

	def movement(self, old_pos, new_pos, max_feedrate):
		self._movement_command_count += 1
		z_change = new_pos["Z"] - old_pos["Z"]
		if 0 < z_change < 1:
			self._z_changes.append(z_change)

	def extrude(self, tool, old_pos, new_pos, extruded_length, max_feedrate):
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

	def extrude(self, tool, old_pos, new_pos, extruded_length, max_feedrate):
		self._stats["extrude_commands"] += 1

		if self._info_hook.region not in [ PrintingRegion.Shell, PrintingRegion.Infill ]:
			self._stats["wrong_region"] += 1
			return

		self._renderer.add_cylinder(old_pos, new_pos)

class GCodeSpeedHook(GCodeHook):
	def __init__(self):
		super().__init__(self)
		self._max_feedrate_mm_per_sec = 0
		self._print_time_secs = 0
		self._min_command_execution_time_secs = 0.04

	@property
	def max_feedrate_mm_per_sec(self):
		return self._max_feedrate_mm_per_sec

	@property
	def print_time_secs(self):
		return self._print_time_secs

	@property
	def print_time_hms(self):
		secs = round(self.print_time_secs)
		return "%d:%02d:%02d" % (secs // 3600, secs % 3600 // 60, secs % 3600 % 60)

	def _calc_max_distance(self, old_pos, new_pos):
		distance_xy_plane = math.sqrt((new_pos["X"] - old_pos["X"]) ** 2 + (new_pos["Y"] - old_pos["Y"]) ** 2)
		distance_yz_plane = math.sqrt((new_pos["Y"] - old_pos["Y"]) ** 2 + (new_pos["Z"] - old_pos["Z"]) ** 2)
		distance_xy_plane = math.sqrt((new_pos["X"] - old_pos["X"]) ** 2 + (new_pos["Z"] - old_pos["Z"]) ** 2)
		max_distance = max(distance_xy_plane, distance_yz_plane, distance_xy_plane)
		return max_distance

	def movement(self, old_pos, new_pos, max_feedrate):
		max_distance_mm = self._calc_max_distance(old_pos, new_pos)
		velocity_mm_per_sec = max_feedrate / 60
		time_secs = max_distance_mm / velocity_mm_per_sec
		time_secs = max(time_secs, self._min_command_execution_time_secs)
		self._print_time_secs += time_secs

	def extrude(self, tool, old_pos, new_pos, extruded_length, max_feedrate):
		velocity_mm_per_sec = max_feedrate / 60
		self._max_feedrate_mm_per_sec = max(self._max_feedrate_mm_per_sec, velocity_mm_per_sec)

class GCodeManipulationHook(GCodeHook):
	def __init__(self):
		super().__init__()
		self._commands = [ ]

	def serialize(self):
		return "\n".join(str(cmd) for cmd in self._commands) + "\n"

class GCodeManipulationRemoveExtrusionHook(GCodeManipulationHook):
	def __init__(self, insert_timing_markers = False, timing_marker_interval = 100):
		super().__init__()
		self._insert_timing_markers = insert_timing_markers
		self._timing_marker_interval = timing_marker_interval
		self._command_count = 0
		self._marker_id = 0

	def command(self, command):
		if self._insert_timing_markers and self._command_count == 0:
			# Insert a command to reset extrusion axis
			self._commands.append(GCodeCommand("G92", "E0"))

		if command.cmd in [ GCodes.SetExtruderNozzleTemperature, GCodes.SetBedTemperature ]:
			# We cannot leave these commands out entirely, since then the
			# printer will say "invalid file format" if they are not received
			# within the first 500 commands
			command["S"] = "0"
		elif command.cmd in [ GCodes.RapidMovement, GCodes.ControlledMovement ]:
			if command.has_arg("E"):
				command.remove_arg("E")
		elif self._insert_timing_markers and (command.cmd == GCodes.SetPositionToValue):
			if command.has_arg("E"):
				command.remove_arg("E")
				if command.arg_count == 0:
					# Omit this command entirely
					return
		self._commands.append(command)

		if self._insert_timing_markers:
			self._command_count += 1
			if (self._command_count % self._timing_marker_interval) == 0:
				# Insert a timing marker
				self._marker_id += 1
				self._commands.append(GCodeCommand("G92", "E%d.%03d" % (self._marker_id // 1000, self._marker_id % 1000)))

class GCodeManipulationInsertProgressHook(GCodeManipulationHook):
	def __init__(self, speed_hook, total_printing_time):
		super().__init__()
		self._speed_hook = speed_hook
		self._total_printing_time = total_printing_time
		self._current_progress = 0

	def command(self, command):
		if command.comment == "percent":
			return

		current_printing_progress_percent = round(100 * self._speed_hook.print_time_secs / self._total_printing_time)
		for i in range(current_printing_progress_percent - self._current_progress):
			self._commands.append(GCodeCommand(cmd_string = None, arg_string = None, comment = "percent"))
		self._current_progress = current_printing_progress_percent
		self._commands.append(command)
