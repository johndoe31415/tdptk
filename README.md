# tdptk
This is a toolkit for handling 3d printer files. It is by no means complete but
has some useful functionality. In particular, it can:

  * Render G-code using POV-ray to create a 3d representation
  * Convert G-code (such as created by Cura) into the GX file format used by
    FlashForge (automatically creating a preview image from the 3d rendered
    G-code)
  * Decompose and recompose FlashForge GX files into its constituent parts
  * Send a GX file to a Flashforge printer on the command line


## Disclaimer
I own a Bresser Rex -- this is essentially a FlashForge Adventurer 3 (also sold
as the "Monoprice Voxel"). All of my development has been tested with that
printer. While I do have included some support for features which my printer
obviously doesn't have (like dual extruders), I have no way to test those.


## License
GNU GPL-3.
