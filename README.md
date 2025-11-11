# CAD-AI Models Repository

This repository contains FreeCAD Python scripts for generating 3D models via the CAD-AI system.

## Structure

```
models/
├── demo/              # Simple demo cube
├── parametric-box/    # Configurable box with parameters
└── your-model/        # Add your models here
```

## How It Works

1. **Create a model**: Add a new folder under `models/` with a `generate.py` script
2. **Push to main**: Commit and push your changes
3. **Automatic generation**: GitHub Actions triggers AWS Fargate to generate STL files
4. **View in browser**: Model appears at https://d2j2tqi3nk8zjp.cloudfront.net

## Adding a New Model

1. Create folder: `mkdir models/my-model`
2. Create script: `models/my-model/generate.py`
3. Write FreeCAD Python code (see examples below)
4. Commit and push

## Example Scripts

### Simple Cube (Demo)

```python
import FreeCAD
import Part

def generate_model():
    doc = FreeCAD.newDocument("Demo")
    cube = Part.makeBox(100, 100, 100)
    obj = doc.addObject("Part::Feature", "Cube")
    obj.Shape = cube
    doc.recompute()
    return doc

if __name__ == "__main__":
    generate_model()
```

### Parametric Box

```python
import FreeCAD
import Part

def generate_model(length=150, width=100, height=50, wall=3):
    doc = FreeCAD.newDocument("Box")

    # Outer box
    outer = Part.makeBox(length, width, height)

    # Inner cavity
    inner = Part.makeBox(
        length - 2*wall,
        width - 2*wall,
        height - wall,
        FreeCAD.Vector(wall, wall, wall)
    )

    # Create hollow box
    box = outer.cut(inner)

    obj = doc.addObject("Part::Feature", "Box")
    obj.Shape = box
    doc.recompute()
    return doc

if __name__ == "__main__":
    generate_model()
```

## Manual Trigger

You can manually trigger model generation:

1. Go to **Actions** tab
2. Select **Generate CAD Model** workflow
3. Click **Run workflow**
4. Enter model name and version
5. Click **Run**

## Monitoring

- **CloudWatch Logs**: Check AWS CloudWatch for generation logs
- **S3 Status**: Check `s3://cad-dev-models-aod1lux5/models/{model}/{version}/status.json`
- **Frontend**: View model at `https://d2j2tqi3nk8zjp.cloudfront.net/models/{model}/{version}`

## Documentation

- [FreeCAD Python Scripting](https://wiki.freecad.org/Python_scripting_tutorial)
- [CAD-AI Main Repository](https://github.com/reindervandervoort/CAD-AI)
- [Models Repository Guide](https://github.com/reindervandervoort/CAD-AI/blob/main/MODELS_REPOSITORY_GUIDE.md)

## Cost

Each model generation costs approximately $0.01 (5 minutes of Fargate runtime).

## Support

For issues with model generation, check:
1. CloudWatch logs: `/ecs/cad-dev-freecad`
2. Status file in S3
3. Create issue in main CAD-AI repository
