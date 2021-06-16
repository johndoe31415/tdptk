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

import sys
from .MultiCommand import MultiCommand
from .ActionFileInfo import ActionFileInfo
from .ActionPrinterStatus import ActionPrinterStatus
from .ActionGerberCommand import ActionGerberCommand
from .ActionMergeGX import ActionMergeGX
from .ActionSplitGX import ActionSplitGX
from .ActionCreateGX import ActionCreateGX
from .ActionPrint import ActionPrint
from .ActionRender import ActionRender
from .XGCodeFile import XGCodeMaterials

def _dimensions(text):
	if "x" in text:
		(width, height) = text.split("x")
		return (int(width), int(height))
	else:
		return (int(text), int(text))

def main():
	mc = MultiCommand()

	def genparser(parser):
		parser.add_argument("-t", "--filetype", choices = [ "auto", "g", "gx", "stl" ], default = "auto", help = "Filetype to assume for the file to be analyzed. Can be any of %(choices)s, defaults to %(default)s. 'auto' guesses the filetype based on the file name extension.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity during the importing process.")
		parser.add_argument("filename", nargs = "+", help = "File(s) to analyze")
	mc.register("fileinfo", "Display information about a file", genparser, action = ActionFileInfo, aliases = [ "info" ])

	def genparser(parser):
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity during the importing process.")
		parser.add_argument("uri", nargs = "+", help = "Printer(s) to connect to, using a scheme such as ff://myprinter for the FlashForge protocol")
	mc.register("status", "Display status of connected printer(s)", genparser, action = ActionPrinterStatus)

	def genparser(parser):
		parser.add_argument("-t", "--timeout", metavar = "secs", type = float, default = 1.0, help = "Command timeout in seconds, defaults to %(default).1f sec")
		parser.add_argument("-u", "--uri", metavar = "uri", required = True, help = "Printer to connect to, using a scheme such as ff://myprinter for the FlashForge protocol")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity during the importing process.")
		parser.add_argument("commands", nargs = "+", help = "Gerber command(s) to execute")
	mc.register("cmd", "Directly execute a Gerber command", genparser, action = ActionGerberCommand)

	def genparser(parser):
		parser.add_argument("-f", "--force", action = "store_true", help = "Overwrite output files even if they already exists.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity during the importing process.")
		parser.add_argument("gx_filename", help = ".gx file to read")
		parser.add_argument("json_metadata_filename", help = "JSON metadata filename")
		parser.add_argument("preview_bmp_filename", help = "Preview bitmap filename")
		parser.add_argument("gcode_filename", help = "G-code instructions filename")
	mc.register("split-gx", "Split a .gx file into metadata, preview bitmap and Gerber data", genparser, action = ActionSplitGX)

	def genparser(parser):
		parser.add_argument("-f", "--force", action = "store_true", help = "Overwrite output file even if it already exists.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity during the importing process.")
		parser.add_argument("json_metadata_filename", help = "JSON metadata filename")
		parser.add_argument("preview_bmp_filename", help = "Preview bitmap filename")
		parser.add_argument("gcode_filename", help = "G-code instructions filename")
		parser.add_argument("gx_filename", help = ".gx file to create by merging the aforementioned files")
	mc.register("merge-gx", "Merge a .gx file from metadata, preview bitmap and Gerber data", genparser, action = ActionMergeGX)

	def genparser(parser):
		parser.add_argument("--material-right", metavar = "name", type = XGCodeMaterials, default = XGCodeMaterials.PLA, help = "Material used in right extruder. Can be one of %s. Defaults to PLA." % (", ".join(material.name for material in XGCodeMaterials)))
		parser.add_argument("--material-left", metavar = "name", type = XGCodeMaterials, default = XGCodeMaterials.PLA, help = "Material used in right extruder. Can be one of %s. Defaults to PLA." % (", ".join(material.name for material in XGCodeMaterials)))
		parser.add_argument("-f", "--force", action = "store_true", help = "Overwrite output file even if it already exists.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity during the importing process.")
		parser.add_argument("gcode_filename", help = "G-code instructions filename")
		parser.add_argument("gx_filename", help = ".gx file to create from the G-code")
	mc.register("create-gx", "Create a .gx file from Gerber data", genparser, action = ActionCreateGX, aliases = [ "mkgx" ])

	def genparser(parser):
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity during the importing process.")
		parser.add_argument("input_filename", help = "Printer filename, can be of different formats (e.g., must be a .gx file for FlashForge)")
		parser.add_argument("printer_uri", help = "Printer URI to print at")
	mc.register("print", "Print a file on a 3d printer", genparser, action = ActionPrint)

	def genparser(parser):
		parser.add_argument("-m", "--mode", choices = [ "fast", "default" ], default = "default", help = "Rendering modes. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-p", "--povray", metavar = "option", action = "append", default = [ ], help = "Pass this option to the POV-Ray renderer verbatim. Can be specified multiple times.")
		parser.add_argument("-d", "--dimensions", metavar = "width x height", type = _dimensions, default = "800x600", help = "Ouptut image dimensions. Defaults to %(default)s.")
		parser.add_argument("-s", "--style", choices = [ "color", "bw" ], default = "color", help = "Render a particular style. Can be one of %(choices)s, defaults to %(default)s.")
		parser.add_argument("-o", "--oversample", metavar = "factor", type = float, default = 1, help = "Oversample POV-Ray rendering.")
		parser.add_argument("-f", "--force", action = "store_true", help = "Overwrite output file even if it already exists.")
		parser.add_argument("-t", "--filetype", choices = [ "auto", "g", "gx" ], default = "auto", help = "Filetype to assume for the file to be analyzed. Can be any of %(choices)s, defaults to %(default)s. 'auto' guesses the filetype based on the file name extension.")
		parser.add_argument("--show", action = "store_true", help = "Display the POV-ray rendering output in a window")
		parser.add_argument("--no-trim", action = "store_true", help = "By default, the POV-ray output is trimmed and resized appropriately afterwards. With this option, the POV-ray output is directly emitted.")
		parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Increase verbosity during the importing process.")
		parser.add_argument("input_filename", help = "GCode or GXCode input file")
		parser.add_argument("output_filename", help = "Output file to write; automatically determines file type based on extension. When .pov is specified, renders the POV-Ray source")
	mc.register("render", "Do a 3d rendering of GCode using POV-Ray", genparser, action = ActionRender)

	mc.run(sys.argv[1:])
