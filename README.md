# pexpo
*pexpo is a PyxelEdit animation and tileset exporter, incorporating basic texture packing*

[PyxelEdit](http://pyxeledit.com/) is a lovely little pixel editor that excels when producing tile-sets and animations.

It has some built-in export options which let you export images, animations, and tilesets as PNGs, but has nothing to let you export associated meta-data (e.g. time delay between frames).

Additionally it's a common requirement for most pixelly games to want to assemble individual PNGs into spritesheets for faster rendering.

Luckily PyxelEdit has the sanest file format of any tool I've ever used. A PyxelEdit file (`.pyxel`) is simply a zipped collection of PNG files plus a JSON data file.

This Python script is pretty simple and was written specifically for my own purposes, but I'm sharing it here as it may prove useful for someone else, even if only as a starting point.

Warning: It's not pretty :)

## Usage
```
usage: pexpo [-h] [-t] -o <file> <path>

Export PNGs and meta-data from PyxelEdit files.

positional arguments:
  <path>                path to pyxel files (directory or single file)

optional arguments:
  -h, --help            show this help message and exit
  -t, --tileset         generate tileset instead of spritesheet
  -o <file>, --out <file>
                        filename of assembled PNG
```
By default, pexpo loops through animation definitions, generating names (based on the filename plus the animation name) and packing them into a spritesheet. It will output a single PNG plus an XML file listing each sprite with its sheet coordinates and other data, such as time delays (listed in the  `<anims>` element in the XML metadata).

If no animations exist, the script will export sprites from tiles chopped out of the canvas (listed in the  `<sprites>` element in the XML metadata).

Currently the script only picks image data from the first layer (I will add layer composition shortly).

(**Note** As this was written for my own purposes there is some special handling for any layer named 'mask'. Such a layer will be exported separately and the sprite coordinates specified as `mx` and `my` attributes in the parent sprite element.)

Alternatively the script can be run to export a tileset (using the `-t` flag). The width of the output PNG is set to the same as that defined in PyxelEdit. No metadata file is produced in this mode, as the expected use is as a zero-based index into the tileset.

The texture packing algorithm is an exceptionally stupid, but fast and effective, method whereby it simply sorts sprites by height and does scanline detection to find a space.

One final warning. The PyxelEdit file format is undocumented and probably changes between releases. The script has been used with PyxelEdit version 0.3.108.

## Example output spritesheet XML

```
<?xml version="1.0"?>
<spritesheet image="sprites.png">
  <anims>
    <a name="banana-spin">
      <s d="100" h="9" w="9" x="103" y="97"/>
      <s d="100" h="9" w="9" x="191" y="99"/>
      ...
    </a>
    ...
  </anims>
  <sprites>
    <sprite name="thingwithamask">
      <s h="11" mx="142" my="90" w="7" x="135" y="90"/>
      ...
    </sprite>
    ...
  </sprites>
</spritesheet>
```
