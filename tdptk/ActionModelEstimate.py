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
import collections
import json
import scipy.optimize
import time
import datetime
from .BaseAction import BaseAction
from .BenchmarkingTools import BenchmarkingTools
from .GCodeHelpers import GCodeHelpers
from .GCodeInterpreter import GCodeSpeedHook

class ActionModelEstimate(BaseAction):
	def _objective(self, parameter_set):
		model_parameters = { param.name: current_value for (param, current_value) in zip(GCodeSpeedHook.ModelParameters, parameter_set) }
		for param in GCodeSpeedHook.ModelParameters:
			if param.constraints is not None:
				for constraint in param.constraints:
					if not constraint(model_parameters):
						return float("inf")

		estimated_plot = self._create_yxplot(GCodeHelpers.estimate_gcode_timing(self._gcode, model_parameters))
		error = self._estimate_error(estimated_plot, self._reference_plot)
		if self._args.verbose >= 1:
			print(model_parameters, error)
		return error

	def _estimate_error(self, dataset_a, dataset_b):
		error = 0
		for (x_ref, y_ref) in dataset_a.items():
			if x_ref in dataset_b:
				y_est = dataset_b[x_ref]
				error += (y_ref - y_est) ** 2
		return error

	def _create_yxplot(self, data):
		result = { }
		for (x, y) in zip(data["x"], data["y"]):
			if y not in result:
				result[y] = x
		return result

	def run(self):
		if not self._args.force:
			if os.path.exists(self._args.parameter_output_filename):
				print("Refusing to overwrite: %s" % (self._args.parameter_output_filename))
				sys.exit(1)

		t0 = time.time()
		with open(self._args.gcode_filename) as f:
			self._gcode = f.read()
		self._reference_plot = self._create_yxplot(BenchmarkingTools.read_benchmark_file(self._args.benchmark_filename))

		bounds = tuple((param.minvalue, param.maxvalue) for param in GCodeSpeedHook.ModelParameters)
		result = scipy.optimize.differential_evolution(self._objective, bounds)
		t1 = time.time()

		parameter_dict = collections.OrderedDict([ (param.name, approx_value) for (param, approx_value) in zip(GCodeSpeedHook.ModelParameters, result["x"]) ])
		parameter_dict["_metadata"] = {
			"finish_ts_utc":	datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
			"time_taken_secs": t1 - t0,
			"eval": {
				"message":						result["message"],
				"number_function_evaluations":	result["nfev"],
				"success":						result["success"],
			}
		}
		with open(self._args.parameter_output_filename, "w") as f:
			json.dump(parameter_dict, f, indent = 4)
			f.write("\n")
