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

import json

class BenchmarkingTools():
	@classmethod
	def read_benchmark_file(cls, filename):
		points = {
			"x": [ ],
			"y": [ ],
		}
		with open(filename) as f:
			filestate = "pre_data"
			for line in f:
				line = json.loads(line)
				(x, y) = (line["trel"], line["A"])

				if (filestate == "pre_data") and (y > 0):
					filestate = "data"

				if (filestate == "data") and (y == 0):
					break

				if filestate == "data":
					points["x"].append(x)
					points["y"].append(y)
			return points

