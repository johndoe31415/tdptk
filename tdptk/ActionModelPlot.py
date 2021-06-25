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
import json
import bokeh.models
import bokeh.plotting
import bokeh.io
import bokeh.server.server
from .BaseAction import BaseAction
from .BenchmarkingTools import BenchmarkingTools
from .GCodeHelpers import GCodeHelpers
from .GCodeInterpreter import GCodeSpeedHook

class ActionModelPlot(BaseAction):
	def _update_data(self, attr, old, new):
		for (name, control) in self._controls.items():
			self._parameters[name] = control.value
		self._source_estimate.data = GCodeHelpers.estimate_gcode_timing(self._gcode, self._parameters)

	def _create_bokeh_plot(self, doc):
		source_reference = bokeh.models.ColumnDataSource(data = self._reference_plot)
		self._source_estimate = bokeh.models.ColumnDataSource(data = GCodeHelpers.estimate_gcode_timing(self._gcode, self._parameters))
		self._plot = bokeh.plotting.figure(width = 1280, height = 720, title = "3d Printer Time Estimate", tools = "crosshair,pan,reset,save,wheel_zoom")
		self._plot.line("x", "y", source = source_reference, line_width = 2, line_alpha = 0.6, line_color = "red")
		self._plot.line("x", "y", source = self._source_estimate, line_width = 2, line_alpha = 0.6)

		self._controls = collections.OrderedDict([
				(param.name, bokeh.models.Slider(title = param.name, value = self._parameters[param.name], start = param.minvalue, end = param.maxvalue, step = (param.maxvalue - param.minvalue) / 100))
				for param in GCodeSpeedHook.ModelParameters
		])
		for control in self._controls.values():
			control.on_change("value", self._update_data)

		menu = bokeh.layouts.column(*self._controls.values())
		doc.add_root(bokeh.layouts.row(menu, self._plot, width = 1700))
		doc.title = "Time Estimate"

	def _start_bokeh_server(self):
		server = bokeh.server.server.Server({ "/": self._create_bokeh_plot })
		server.start()
		server.io_loop.add_callback(server.show, "/")
		server.io_loop.start()

	def run(self):
		with open(self._args.gcode_filename) as f:
			self._gcode = f.read()
		self._reference_plot = BenchmarkingTools.read_benchmark_file(self._args.benchmark_filename)
		if self._args.model is None:
			model = { }
		else:
			with open(self._args.model) as f:
				model = json.load(f)
		self._parameters = { param.name: model.get(param.name, param.default) for param in GCodeSpeedHook.ModelParameters }
		self._start_bokeh_server()
