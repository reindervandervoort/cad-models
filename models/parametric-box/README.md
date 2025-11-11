# Parametric Box Model

A hollow box with configurable dimensions and wall thickness.

## Description

This model demonstrates parametric design in FreeCAD. The box dimensions and wall thickness can be easily modified by changing variables at the top of `generate.py`.

## Parameters

Default values:
- **Length**: 150mm
- **Width**: 100mm
- **Height**: 50mm
- **Wall Thickness**: 3mm

## Parts

- `HollowBox`: Single hollow box created by boolean subtraction

## Customization

Edit `generate.py` and modify these values:

```python
length = 150  # Change this
width = 100   # Change this
height = 50   # Change this
wall = 3      # Change this
```

Then commit and push to regenerate with new dimensions.

## Expected Output

Three STL files with different detail levels:
- `hollowbox_low.stl`
- `hollowbox_medium.stl`
- `hollowbox_high.stl`

## Use Cases

- Storage containers
- Electronic enclosures
- Organizer trays
- Custom packaging
