# IDragon Blender Tools #
Blender (3.0+) addon for importing mesh files (\*.MSH), mainly from game <i><b>I of the Dragon</b> (2002)</i> by Primal Software.    

Currently work in progress.    

## Current Status
VERSION: 0.6.0

Supported Features: 
 * Full meshes import (with normals, weights, UVs, etc.)
 * Full bones import
 * Textures import (with material setup)
 * Bounding planes import
 * Merge meshes (by groups / materials)
 * Drag & drop import (Blender 4.1+ required) and multiple import
 
Work In Progress: 
 * Animation files (\*.ANM) import

## Details

![Blender Screenshot](IMAGES/Screenshot.png)

### Installation & Configuration
 1. Download the addon from [releases](https://github.com/XenonBaruku/IDragon-Blender-Tools/releases), or download the repository as ZIP, then install like usual Blender addons.
 2. Config unpacked textures directory in addon preferences.
 ![Addon Preferences](IMAGES/AddonPreferences.png)
 3. Check <b>File > Import</b>, there should be a new item named <b><i>The I of the Dragon</i></b>, with all supported file types in it.

### MSH Import
<b>Import Settings</b>    

![Import Settings](IMAGES/ImportSettings.png)

<b>Operator Presets</b>: Apply presets of import settings. Use <b>+</b> or <b>-</b> button to create or delete custom presets.

<b>Merge Mesh Parts</b>: Choose whether merge imported mesh parts or not, and how those mesh parts are merged. 
 * <b>None</b> - Do not merge mesh parts
 * <b>By Groups</b> - Merge mesh parts by group IDs
 * <b>By Textures</b> - Merge mesh parts by textures used

<b>Import Bounding Planes</b>: Import 2D planes data stored in MSH files that likely to be bounds.

<b>Import Textures</b>: Whether import textures (and setup materials) or not. Note that textures directory in addon preferences must be set in order to use this.

<b>Texture Interpolation</b>: Interpolation mode for imported textures. Only available when <b>Import Textures</b> is ON.

## Credits
 * Great thanks to [AlexKimov](https://github.com/AlexKimov) for their research and tools provided at [their repository](https://github.com/AlexKimov/primal-file-formats).
 * The addon was developed with reference to some other addons. Thanks to them and developers of those addons.
