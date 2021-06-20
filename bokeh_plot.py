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
import collections
import bokeh.models
import bokeh.plotting
import bokeh.io

class BokehPlotter():
	def __init__(self, gx_filename, reference_benchmark_filename):
		self._gx_filename = gx_filename
		self._reference_benchmark_file = reference_benchmark_filename
		self._reference_plot = self._read_reference_plot()
		self._parameters = {
			"min_command_execution_time_secs": 0.04,
		}
		self._controls = None

	def _read_reference_plot(self):
		points = {
			"x": [ ],
			"y": [ ],
		}
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
					points["x"].append(x)
					points["y"].append(y)
			return points

	def _create_estimated_plot(self):
		with open("model.json", "w") as f:
			json.dump(self._parameters, f)
		subprocess.check_call([ "./tdptk.py", "info", "-f", "-s", "output.json", "-m", "model.json", self._gx_filename ])
		with open("output.json") as f:
			return json.load(f)

	def _update_data(self, attr, old, new):
		for (name, control) in self._controls.items():
			self._parameters[name] = control.value
		self._source_estimate.data = self._create_estimated_plot()

	def plot(self):
		source_reference = bokeh.models.ColumnDataSource(data = self._reference_plot)
		self._source_estimate = bokeh.models.ColumnDataSource(data = self._create_estimated_plot())
		self._plot = bokeh.plotting.figure(width = 1280, height = 720, title = "3d Printer Time Estimate", tools = "crosshair,pan,reset,save,wheel_zoom")
		self._plot.line("x", "y", source = source_reference, line_width = 2, line_alpha = 0.6)
		self._plot.line("x", "y", source = self._source_estimate, line_width = 2, line_alpha = 0.6)

		self._controls = collections.OrderedDict((
			("min_command_execution_time_secs", bokeh.models.Slider(title = "min_command_execution_time_secs", value = self._parameters["min_command_execution_time_secs"], start = 0, end = 0.1, step = 0.001)),
		))
		for control in self._controls.values():
			control.on_change("value", self._update_data)

		menu = bokeh.layouts.column(*self._controls.values())

		bokeh.io.curdoc().add_root(bokeh.layouts.row(menu, self._plot, width = 1700))
		bokeh.io.curdoc().title = "Time Estimate"


plotter = BokehPlotter("timing/timing.gx", "timing/benchmark.txt")
plotter.plot()
