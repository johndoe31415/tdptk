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

from .NamedStruct import NamedStruct

_STL_Header = NamedStruct((
	("80s",		"header"),
	("L",		"triangle_count"),
))

_STL_Triangle = NamedStruct((
	("f",		"normal_x"),
	("f",		"normal_y"),
	("f",		"normal_z"),
	("f",		"vertex1_x"),
	("f",		"vertex1_y"),
	("f",		"vertex1_z"),
	("f",		"vertex2_x"),
	("f",		"vertex2_y"),
	("f",		"vertex2_z"),
	("f",		"vertex3_x"),
	("f",		"vertex3_y"),
	("f",		"vertex3_z"),
	("H",		"attribute_byte_count"),
))

class STLFile():
	def __init__(self):
		self._triangles = [ ]

	def append(self, triangle):
		self._triangles.append(triangle)

	@classmethod
	def read(cls, filename):
		stl_file = cls()

		with open(filename, "rb") as f:
			header = _STL_Header.unpack_from_file(f)
			for i in range(header.triangle_count):
				triangle = _STL_Triangle.unpack_from_file(f)
				stl_file.append(triangle)
		return stl_file

	def __iter__(self):
		return iter(self._triangles)
