# MMD Tools Append Developer Guide

This guide gives a quick, practical overview for contributors.
If something is not stated here, follow the main [MMD Tools Developer Guide](https://github.com/MMD-Blender/blender_mmd_tools/blob/main/DEVELOPER_GUIDE.md).

## Project Scope

### Core Principles
- Stay lightweight (only append / enhance assets, do not duplicate MMD Tools core)
- Prefer reuse over re‑implementation

### Supported Features
1. Asset search & append
2. TBD

### Out of Scope
1. **MMD Core Functionality** - Should be implemented in [MMD Tools](https://github.com/MMD-Blender/blender_mmd_tools)

## Development Environment

### Prerequisites
- Ensure you have a matching version of Blender for the target development branch
- Use the correct Python version for your Blender release
- Get GitHub access to the [MMD Tools Append repository](https://github.com/MMD-Blender/blender_mmd_tools_append)

| Blender Version | MMD Tools Append Version | Python Version | Branch      |
|-----------------|--------------------------|---------------:|-------------|
| Blender 5.2 LTS | MMD Tools Append v4.x    |           3.13 | [main](https://github.com/MMD-Blender/blender_mmd_tools_append) |
| Blender 4.5 LTS | MMD Tools Append v4.x    |           3.11 | [main](https://github.com/MMD-Blender/blender_mmd_tools_append) |
| Blender 3.6 LTS | MMD Tools Append v1.x    |           3.10 | [blender-v3](https://github.com/MMD-Blender/blender_mmd_tools_append/tree/blender-v3) |

## Project Structure
```
blender_mmd_tools_append/
├── mmd_tools_append/
│   ├── asset_search/   # Asset search & append
│   ├── checkers/       # Validation utilities
│   ├── converters/     # Focused data transforms
│   ├── editors/        #
│   ├── externals/      # Vendored 3rd-party (each with README.txt)
│   ├── generators/     #
│   ├── tuners/         #
│   └── typings/        # .pyi type hints
└── docs/               # (Reserved)
```

## Coding Standards

### Python Style
- Add the following comment block at the top of each Python file:
  ```
  # Copyright {year} MMD Tools Append authors
  # This file is part of MMD Tools Append.
  ```
- Follow [MMD Tools Python Style](https://github.com/MMD-Blender/blender_mmd_tools/blob/main/DEVELOPER_GUIDE.md#python-style)

### Translating the Extension
We use [Manage UI Translations addon](https://developer.blender.org/docs/handbook/translating/translator_guide/#manage-ui-translations-add-on) suggested by Blender.
However, if you want to simply modify only the translated strings, you can ignore this section and directly edit the [`m17n.py`](mmd_tools_append/m17n.py) file.
For more details, check out [MMD Tools Developer Guide](https://github.com/MMD-Blender/blender_mmd_tools/blob/main/DEVELOPER_GUIDE.md#translating-the-extension).

#### Easier, safer method
Instead of editing `m17n.py` directly, we recommend using [Poedit](https://poedit.com) to edit the .po files located in [`locales`](locales) folder.
To test the translation, download and put [po_to_m17n.py](https://gist.github.com/ulyssas/f28c53790ca5f234f10ba8d18fd948c8) into the `locales` folder.
When you run the script in Python, `m17n.py` will be updated according to the edited .po files. (You need Python 3.11 or later)

You can submit the translation by creating [issues](https://github.com/MMD-Blender/blender_mmd_tools_append/issues) and uploading the .po file. (Or create Pull Request if you know how to do it)
But do not upload the generated `m17n.py`, as it has different content and structure from the original file.

#### Process
1. Download the repository via zip (green `Code` button).
2. Move `mmd_tools_append` folder to `Blender/[BLENDER_VERSION]/extensions/user_default/mmd_tools_append`.
3. Edit the .po files in the `locales` folder using Poedit.
4. Place `po_to_m17n.py` inside `locales` folder then execute the script in the terminal:

Example command (Windows):
```
cd Downloads/blender_mmd_tools_append-main/locales
python po_to_m17n.py -a "%APPDATA%/Blender Foundation/Blender/5.2/extensions/user_default/mmd_tools_append"
```

macOS:
```
cd Downloads/blender_mmd_tools_append-main/locales
python3 po_to_m17n.py -a "~/Library/Application Support/Blender/5.2/extensions/user_default/mmd_tools_append"
```

5. Check the translation in Blender. Make sure to restart Blender if it was already opened.

## Release Process
Releases may be performed by maintainers who meet both of the following requirements:
- Management permissions on this repository
- A [Blender Extensions](https://extensions.blender.org/add-ons/mmd-tools/) account and membership in the [MMD team](https://extensions.blender.org/team/mmd/)

1. Tag the commit in `main` with the version number (`vMAJOR.MINOR.PATCH`)
2. Pushing the tag triggers a GitHub Action that builds artifacts and creates a draft release
3. Manually finalize and publish the GitHub Release draft
4. Manually upload the artifacts to [Blender Extensions](https://extensions.blender.org/add-ons/mmd-tools-append/)

## Getting Help
If you need help with development:
- Ask questions in the [MMD & Blender Discord Server](https://discord.gg/zRgUkuaPWw) `#addon-development` channel
- Open an issue to discuss implementation details
- Refer to existing code for patterns and approaches

We appreciate your contributions and look forward to working together to improve MMD Tools Append!
