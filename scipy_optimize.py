#!/usr/bin/python3
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
import subprocess
import scipy.optimize
from tdptk.GCodeInterpreter import GCodeSpeedHook

class ModelFinder():
	def __init__(self, gx_filename, reference_benchmark_filename):
		self._gx_filename = gx_filename
		self._reference_benchmark_file = reference_benchmark_filename
		self._bounds = tuple((param.minvalue, param.maxvalue) for param in GCodeSpeedHook.ModelParameters)
		self._reference_plot = self._read_reference_plot()

	def _read_reference_plot(self):
		points = { }
		with open(self._reference_benchmark_file) as f:
			filestate = "pre_data"
			for line in f:
				line = json.loads(line)
				(x, y) = (line["trel"], line["A"])

				if (filestate == "pre_data") and (y > 0):
					filestate = "data"

				if (filestate == "data") and (y == 0):
					break

				if filestate == "data":
					if y not in points:
						points[y] = x
			return points

	def _create_estimated_plot(self):
		with open("model.json", "w") as f:
			json.dump(self._parameters, f)
		subprocess.check_call([ "./tdptk.py", "info", "-f", "-s", "output.json", "-m", "model.json", self._gx_filename ])
		with open("output.json") as f:
			json_data = json.load(f)
			points = { }
			for (x, y) in zip(json_data["x"], json_data["y"]):
				if y not in points:
					points[y] = x
			return points

	def _objective(self, parameter_set):
		parameter_dict = { param.name: current_value for (param, current_value) in zip(GCodeSpeedHook.ModelParameters, parameter_set) }

		for param in GCodeSpeedHook.ModelParameters:
			if param.constraints is not None:
				for constraint in param.constraints:
					if not constraint(parameter_dict):
						return float("inf")

		self._parameters = parameter_dict

		reference_plot = self._reference_plot
		estimated_plot = self._create_estimated_plot()

		error = 0
		for (x_ref, y_ref) in reference_plot.items():
			if x_ref in estimated_plot:
				y_est = estimated_plot[x_ref]
				error += (y_ref - y_est) ** 2

		print(parameter_dict, error)
		return error

	def optimize(self):
		result = scipy.optimize.differential_evolution(self._objective, self._bounds)
		print(result)

finder = ModelFinder("timing/timing.gx", "timing/benchmark.txt")
finder.optimize()


