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

## Release Process
Currently, only @UuuNyaa has permission to perform release tasks:

1. Tag the commit in `main` with the version number (`vMAJOR.MINOR.PATCH`)
2. Pushing the tag triggers a GitHub Action that builds artifacts and creates a draft release
3. Manually finalize and publish the GitHub Release draft
4. Manually upload the artifacts to [Blender Extensions](https://extensions.blender.org/add-ons/mmd-tools-append/)
