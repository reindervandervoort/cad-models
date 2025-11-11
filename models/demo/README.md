# Demo Model - Simple Cube

A simple 100x100x100mm cube to test the CAD-AI pipeline.

## Description

This is the simplest possible FreeCAD model - a single cube. It's used to verify that the entire pipeline works:
- GitHub Actions workflow triggers
- Fargate task starts
- FreeCAD script executes
- STL files are generated (low, medium, high detail)
- Files are uploaded to S3
- Frontend can display the model

## Parameters

- **Size**: 100mm on all sides
- **Origin**: (0,0,0)
- **Material**: N/A (just geometry)

## Parts

- `Cube`: Single solid cube

## Expected Output

Three STL files:
- `cube_low.stl` (~500 triangles)
- `cube_medium.stl` (~5,000 triangles)
- `cube_high.stl` (~20,000 triangles)

## Usage

Automatically generated when code is pushed to this repository, or manually triggered via GitHub Actions.
