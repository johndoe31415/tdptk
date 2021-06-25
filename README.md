# tdptk
This is a toolkit for handling 3d printer files. It is by no means complete but
has some useful functionality. In particular, it can:

  * Render STL or G-code using POV-Ray to create a 3d representation
  * Convert G-code (such as created by Cura) into the GX file format used by
    FlashForge (automatically creating a preview image from the 3d rendered
    G-code)
  * Decompose and recompose FlashForge GX files into its constituent parts
  * Send a GX file to a Flashforge printer on the command line
  * Manipulate G-code (e.g., strip all heating and extrusion commands to be
    able to perform a 'dry run')

## Usage
Simply call the command line application, it will guide you with some help pages. For example:

```
$ ./tdptk.py 
Syntax: ./tdptk.py [command] [options]

Available commands:

Options vary from command to command. To receive further info, type
    ./tdptk.py [command] --help
    fileinfo           Display information about a file
    status             Display status of connected printer(s)
    gerber             Directly execute a Gerber command
    command            Execute a printer command such as stopping the print or
                       querying information
    split-gx           Split a .gx file into metadata, preview bitmap and
                       Gerber data
    merge-gx           Merge a .gx file from metadata, preview bitmap and
                       Gerber data
    create-gx          Create a .gx file from Gerber data
    print              Print a file on a 3d printer
    render             Do a 3d rendering of GCode using POV-Ray
    manipulate         Manipulate G-Code, e.g., by removing all
                       extrusion/heating commands
    model-plot         Use Bokeh to serve an application which plots a model
                       estimate against real output
    model-estimate     Use a differntial evolution approach in SciPy to
                       estimate model parameters

$ ./tdptk.py render --help
usage: ./tdptk.py render [-m {fast,default}] [-p option] [-d width x height]
                         [-s {color,bw}] [-o factor] [-f] [-t {auto,g,gx}]
                         [--show] [--no-trim] [-v] [--help]
                         input_filename output_filename

Do a 3d rendering of GCode using POV-Ray

positional arguments:
  input_filename        GCode or GXCode input file
  output_filename       Output file to write; automatically determines file
                        type based on extension. When .pov is specified,
                        renders the POV-Ray source

optional arguments:
  -m {fast,default}, --mode {fast,default}
                        Rendering modes. Can be one of fast, default, defaults
                        to default.
  -p option, --povray option
                        Pass this option to the POV-Ray renderer verbatim. Can
                        be specified multiple times.
  -d width x height, --dimensions width x height
                        Ouptut image dimensions. Defaults to 800x600.
  -s {color,bw}, --style {color,bw}
                        Render a particular style. Can be one of color, bw,
                        defaults to color.
  -o factor, --oversample factor
                        Oversample POV-Ray rendering.
  -f, --force           Overwrite output file even if it already exists.
  -t {auto,g,gx}, --filetype {auto,g,gx}
                        Filetype to assume for the file to be analyzed. Can be
                        any of auto, g, gx, defaults to auto. 'auto' guesses
                        the filetype based on the file name extension.
  --show                Display the POV-Ray rendering output in a window
  --no-trim             By default, the POV-Ray output is trimmed and resized
                        appropriately afterwards. With this option, the POV-
                        Ray output is directly emitted.
  -v, --verbose         Increase verbosity during the importing process.
  --help                Show this help page.
```

## Benchmarking a Machine
To accurately estimate the time a print takes, the machine needs to be modeled.
This means, the specific constraints under which move or extrude operations
occur need to be estimated. This is not straightforward and small errors add up
through thousands of Gerber commands.

tdptk takes this approach to this problem: We first take a real-world print
file, which can be arbitrary but should contain as much operations as happens
in the real world (e.g., many small movements, but also some large movements).
Then, we strip out all extrusion functionality from this G-code so we can run
it on the actual machine as a "dry run". We also use tdptk to insert G92 codes
every 100 instructions to set the E axis (which is not going to be used in the
dry run) so we can continuously query it outside as a kind of "progress
indicator".

Then, we let the machine print and benchmark it: We query over the network the
"E" position and record timestamps.

This gives us the G-code file we used to print and a benchmark file which
records real-world timings of that G-code. We use this together with scipy's
differential evolution algorithm to estimate a parameter file.

Here's how it's all done. First, preparing a real G-code print file and
transforming it into a "dry-run" G-code file:

```
$ ./tdptk.py manipulate --remove-extrusion --insert-timing-markers input.g dryrun.g
```

Then, benchmarking it (you need to print the dryrun.g file while this runs):

```
$ ./tdptk.py cmd -u ff://myprinter benchmark
```

This creates a file called "benchmark.txt". We use this file to trigger the
differential evolution algorithm:

```
$ ./tdptk.py model-estimate dryrun.g benchmark.txt model_parameters.json
```

Then, we can plot those model parameters and compare how well they stack up
against our real-world measurements:

```
$ ./tdptk.py model-plot -m model_parameters.json dryrun.g benchmark.txt 
```

## Example
This is an example of a rendered STL input:

![3D Rendering of STL](https://raw.githubusercontent.com/johndoe31415/tdptk/master/doc/rendering_stl.png)

Here's an example of a 3D rendering of G-code:

![3D Rendering of G-Code](https://raw.githubusercontent.com/johndoe31415/tdptk/master/doc/rendering_g.png)


## Disclaimer
I own a Bresser Rex -- this is essentially a FlashForge Adventurer 3 (also sold
as the "Monoprice Voxel"). All of my development has been tested with that
printer. While I do have included some support for features which my printer
obviously doesn't have (like dual extruders), I have no way to test those.


## Dependencies
tdptk requires Python3 and mako. If you want to 3D render things, you also need
POV-ray and ImageMagick installed. For the "model-estimate" functionality you
need scipy. For the "model-plot" functionality you need Bokeh. Both
"model-estimate" and "model-plot" facilities will simply not appear when
scipy/Bokeh are not installed, but the remaining functionality of tdptk will
still work.

## License
GNU GPL-3.
