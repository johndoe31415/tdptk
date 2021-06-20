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
    cmd                Directly execute a Gerber command
    split-gx           Split a .gx file into metadata, preview bitmap and
                       Gerber data
    merge-gx           Merge a .gx file from metadata, preview bitmap and
                       Gerber data
    create-gx          Create a .gx file from Gerber data
    print              Print a file on a 3d printer
    render             Do a 3d rendering of GCode using POV-Ray
    manipulate         Manipulate G-Code, e.g., by removing all
                       extrusion/heating commands

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


## License
GNU GPL-3.
