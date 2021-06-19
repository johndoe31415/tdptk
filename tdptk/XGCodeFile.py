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

import collections
import enum
from .NamedStruct import NamedStruct

class XGCodeFlags(enum.IntEnum):
	Use_Right_Extruder = (1 << 0)
	Use_Left_Extruder = (1 << 1)
	MakeRaft = (1 << 2)
	Unknown_Flag4 = (1 << 3)
	Unknown_Flag5 = (1 << 4)
	Unknown_Flag6 = (1 << 5)

	@classmethod
	def decode_bitfield(cls, bitfield):
		flags = [ ]
		for value in cls:
			if (bitfield & value) != 0:
				flags.append(value)
		return flags

class XGCodeMaterials(enum.IntEnum):
	ABS = 0
	PLA = 1
	HIPS = 2
	FlexibleFilament = 4
	PC = 5
	PA = 6
	PETG = 7
	PVA = 8
	ASA = 9
	Wood = 10
	PACF = 11
	PET_CF_9780BK = 12
	PAHT_9825NT = 13
	PETG_CF = 14
	PLA_CF = 15

XGCodeHeader = NamedStruct((
	("16s",		"version"),							# 0x00: static string
	("L",		"offset_bitmap"),					# 0x10:
	("L",		"offset_gcode_right"),				# 0x14:
	("L",		"offset_gcode_left"),				# 0x18:
	("L",		"print_time_secs"),					# 0x1c:
	("L",		"filament_use_mm_right"),			# 0x20:
	("L",		"filament_use_mm_left"),			# 0x24:
	("H",		"print_flags"),						# 0x28: print_flags
	("H",		"layer_height_microns"),			# 0x2a: ((float)print_params + 0xb8) * 1000.0
	("H",		"unknown"),							# 0x2c: ((float)print_params + 0x1ac) * 100.0
	("H",		"perimeter_shell_count"),			# 0x2e: print_params[0x134]
	("H",		"print_speed_mm_per_sec"),			# 0x30: print_params[0xc4]
	("H",		"platform_temp_deg_c"),				# 0x32: print_params[0xe0]
	("H",		"extruder_temp_right_deg_c"),		# 0x34: print_params[0xd4]
	("H",		"extruder_temp_left_deg_c"),		# 0x36: print_params[0xd8]
	("B",		"material_right"),					# 0x38: print_params[0x24]
	("B",		"material_left"),					# 0x39: print_params[0x28]
))

class XGCodeFile():
	_HEADER_V1 = b"xgcode 1.0\n\x00\x00\x00\x00\x00"

	def __init__(self, header, bitmap_data, gcode_data):
		self._header = header
		self._bitmap_data = bitmap_data
		self._gcode_data = gcode_data

	@property
	def header(self):
		return self._header

	@property
	def header_dict(self):
		return collections.OrderedDict((
			("print_time_secs", self._header.print_time_secs),
			("filament_use_mm_right", self._header.filament_use_mm_right),
			("filament_use_mm_left", self._header.filament_use_mm_left),
			("print_flags", self._header.print_flags),
			("layer_height_microns", self._header.layer_height_microns),
			("perimeter_shell_count", self._header.perimeter_shell_count),
			("print_speed_mm_per_sec", self._header.print_speed_mm_per_sec),
			("platform_temp_deg_c", self._header.platform_temp_deg_c),
			("extruder_temp_right_deg_c", self._header.extruder_temp_right_deg_c),
			("extruder_temp_left_deg_c", self._header.extruder_temp_left_deg_c),
			("material_right", self._header.material_right),
			("material_left", self._header.material_left),
		))

	@classmethod
	def from_header_dict(cls, header_dict, bitmap_data, gcode_data):
		header_dict = dict(header_dict)
		header_dict.update({
			"version":				cls._HEADER_V1,
			"offset_bitmap":		XGCodeHeader.size,
			"offset_gcode_right":	XGCodeHeader.size + len(bitmap_data),
			"offset_gcode_left":	XGCodeHeader.size + len(bitmap_data),
			"unknown":				0,
		})
		header = XGCodeHeader.create_fields(header_dict)
		return cls(header = header, bitmap_data = bitmap_data, gcode_data = gcode_data)

	@property
	def bitmap_data(self):
		return self._bitmap_data

	@property
	def gcode_data(self):
		return self._gcode_data

	@property
	def material_left(self):
		return XGCodeMaterials(self._header.material_left)

	@property
	def material_right(self):
		return XGCodeMaterials(self._header.material_right)

	@property
	def flags(self):
		return XGCodeFlags.decode_bitfield(self._header.print_flags)

	@classmethod
	def read(cls, filename):
		with open(filename, "rb") as f:
			header = XGCodeHeader.unpack_from_file(f)
			if header.version != cls._HEADER_V1:
				raise NotImplementedError("Unable to decode .gx file with non-v1.0 header (was: %s)" % (str(header.version)))

			f.seek(header.offset_bitmap)
			bitmap_data = f.read(header.offset_gcode_left - header.offset_bitmap)

			f.seek(header.offset_gcode_left)
			gcode_data = f.read()

		xgcodefile = cls(header = header, bitmap_data = bitmap_data, gcode_data = gcode_data)
		return xgcodefile

	def write(self, filename):
		with open(filename, "wb") as f:
			f.write(XGCodeHeader.pack(self._header))
			f.write(self._bitmap_data)
			f.write(self._gcode_data)
