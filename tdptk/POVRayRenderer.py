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

import math
import subprocess
import tempfile
import enum
import json
import mako.template
from .CmdlineEscape import CmdlineEscape
from .GCodeInterpreter import GCodeBaseInterpreter

class POVRayStyle(enum.Enum):
	BlackWhite = "bw"
	Color = "color"

class POVRayMode(enum.Enum):
	Default = "default"
	Fast = "fast"

_TEMPLATE = mako.template.Template("""\
#version 3.7;
#include "colors.inc"
#include "shapes.inc"

global_settings {
	assumed_gamma 1.0
%if use_photons:
	photons {
		count 1000
	}
%endif
}

%if style == "BlackWhite":
background { color Black }
%elif style == "Color":
background { color White }
%else:
${error("Unknown color style '%s'" % (style))}
%endif

camera {
	orthographic
	location <10, 10, 10>
	right x * image_width / image_height
	look_at  <0, 0, 0>
	angle 60
}

%if style == "BlackWhite":
light_source { <1000, 1000, 1000> color White }
%elif style == "Color":
light_source {
	<15, 7, 15>	color White	spotlight
	radius 1
	jitter
	point_at <0, 0, 0>
	area_light 3*x, 3*z, 4, 4
%if use_photons:
	photons {
		refraction on
		reflection on
	}
%endif
}
%else:
${error("Unknown color style '%s'" % (style))}
%endif

#declare tdp_object = object {
	union {
%for ((x1, y1, z1), (x2, y2, z2)) in cylinders:
		cylinder{ <${x1}, ${z1}, ${y1}>, <${x2}, ${z2}, ${y2}>, ${cylinder_diameter / 2} }
%endfor
%for ((x1, y1, z1), (x2, y2, z2), (x3, y3, z3)) in triangles:
		triangle{ <${x1}, ${z1}, ${y1}>, <${x2}, ${z2}, ${y2}>,  <${x3}, ${z3}, ${y3}> }
%endfor
	}
	texture {
%if style == "BlackWhite":
		pigment { color rgb<0.5, 0.5, 0.5> }
		finish { phong 0.5 }
%elif style == "Color":
		pigment { color rgb<0.853, 0.124, 0.109> }
		normal {
			bumps 0.1
			scale 0.1
		}
		finish {
			phong 0.7
			phong_size 40
			specular 0.8
			roughness 0.15
			diffuse 0.75
		}
%else:
${error("Unknown color style '%s'" % (style))}
%endif
	}
%if use_photons:
	photons {
		target
		refraction on
		reflection on
		collect off
	}
%endif
}

#declare scaling_factor = ${scaling_factor};

#declare pos_top_right = max_extent(tdp_object);
#declare pos_bottom_left = min_extent(tdp_object);
#declare pos_obj_center = (pos_top_right + pos_bottom_left) / 2;
#declare obj_extent = max(pos_top_right.x, pos_top_right.y, pos_top_right.z);

#declare tdp_object = object{tdp_object translate -pos_obj_center }
#declare tdp_object = object{tdp_object scale scaling_factor / obj_extent }

tdp_object
""", strict_undefined = True)

class POVRayRenderer():
	def __init__(self, width = 800, height = 600, cylinder_diameter = 0.4, oversample_factor = 1, style = POVRayStyle.BlackWhite, mode = POVRayMode.Default, verbosity = 0):
		super().__init__()
		assert(isinstance(style, POVRayStyle))
		assert(isinstance(mode, POVRayMode))
		self._width = width
		self._height = height
		self._cylinder_diameter = cylinder_diameter
		self._oversample_factor = oversample_factor
		self._style = style
		self._mode = mode
		self._verbosity = verbosity
		self._cylinders = [ ]
		self._triangles = [ ]

	def add_cylinder(self, old_pos, new_pos):
		old = (old_pos["X"], old_pos["Y"], old_pos["Z"])
		new = (new_pos["X"], new_pos["Y"], new_pos["Z"])
		distance = math.sqrt((old[0] - new[0]) ** 2 + (old[1] - new[1]) ** 2 + (old[2] - new[2]) ** 2)
		if distance > 0:
			self._cylinders.append((old, new))

	def add_triangle(self, vertex1, vertex2, vertex3):
		self._triangles.append((vertex1, vertex2, vertex3))

	def render_source(self):
		def error_fnc(text):
			raise Exception(text)
		if self._verbosity >= 1:
			print("%d cylinders (diameter %.2fmm) and %d triangles to render." % (len(self._cylinders), self._cylinder_diameter, len(self._triangles)))
		args = {
			"scaling_factor":		7,
			"cylinders":			self._cylinders,
			"triangles":			self._triangles,
			"cylinder_diameter":	self._cylinder_diameter,
			"style":				self._style.name,
			"error":				error_fnc,
			"use_photons":			False,
		}
		return _TEMPLATE.render(**args)

	def render_image(self, image_filename, additional_povray_options = None, show_image = False, trim_image = False):
		bg_color = {
			POVRayStyle.BlackWhite:		"black",
			POVRayStyle.Color:			"white",
		}[self._style]

		with tempfile.NamedTemporaryFile(suffix = ".pov", mode = "w") as pov_file, tempfile.NamedTemporaryFile(suffix = ".png") as png_file:
			povray_options = [
				"Width=%d" % (round(self._width * self._oversample_factor)),
				"Height=%d" % (round(self._height * self._oversample_factor)),
				"Output_to_File=true",
				"Output_File_Name=%s" % (png_file.name),
			]
			if not show_image:
				povray_options += [
					"Display=false",
				]
			else:
				povray_options += [
					"Display=true",
					"Pause_When_Done=true",
				]
			if self._mode == POVRayMode.Default:
				povray_options += [
					"Antialias=true",
					"Quality=11",
				]
			elif self._mode == POVRayMode.Fast:
				povray_options += [
					"Antialias=false",
					"Quality=3",
				]
			if additional_povray_options is not None:
				povray_options += additional_povray_options
			pov_file.write(self.render_source())
			pov_file.flush()
			povray_cmdline = [ "povray" ] + povray_options + [ pov_file.name ]
			if self._verbosity >= 3:
				print("Command: %s" % (CmdlineEscape().cmdline(povray_cmdline)))
			subprocess.check_call(povray_cmdline)

			if not trim_image:
				subprocess.check_call([ "convert", "-resize", "%dx%d" % (self._width, self._height), "+repage", png_file.name, image_filename ])
			else:
				with tempfile.NamedTemporaryFile(suffix = ".png") as trimmed_png_file:

					# First we trim the image
					subprocess.check_call([ "convert", "-trim", "+repage", png_file.name, trimmed_png_file.name ])

					# Then we get the current extents of that image
					image_data = json.loads(subprocess.check_output([ "convert", trimmed_png_file.name, "json:-" ]))[0]["image"]
					cropped_geometry = (image_data["geometry"]["width"], image_data["geometry"]["height"])

					# Now find out how we have to pad it to get the correct aspect ratio
					cropped_aspect = cropped_geometry[0] / cropped_geometry[1]
					desired_aspect = self._width / self._height
					if cropped_aspect > desired_aspect:
						desired_geometry = (cropped_geometry[0], round(cropped_geometry[0] / self._width * self._height))
					else:
						desired_geometry = (round(cropped_geometry[1] * self._width / self._height), cropped_geometry[1])

					# Then pad it first and then resize to final dimensions
					subprocess.check_call([ "convert", "-gravity", "center", "-background", bg_color, trimmed_png_file.name, "-extent", "%dx%d" % (desired_geometry[0], desired_geometry[1]), "-resize", "%dx%d" % (self._width, self._height), "+repage", image_filename ])
