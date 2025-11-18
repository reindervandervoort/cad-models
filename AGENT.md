# CAD Models Repository - Agent Instructions

## Purpose

This repository contains FreeCAD Python scripts that generate parametric 3D models. When you push changes to `models/**/*.py`, GitHub Actions automatically triggers AWS Fargate tasks that execute your FreeCAD scripts and generate multi-LOD STL files.

## Repository Architecture

```
models/
├── demo/              # Simple cube demonstration
│   └── main.py       # FreeCAD script (required)
├── parametric-box/   # Hollow box with configurable dimensions
│   └── main.py
├── keyboard/         # Parametric keyboard with 9 keycaps
│   ├── main.py
│   └── input.json    # Optional: external configuration
└── your-model/       # Add new models here
    ├── main.py       # REQUIRED: Must be named main.py
    └── input.json    # OPTIONAL: External parameters
```

## Critical Requirements for FreeCAD Scripts

### 1. File Naming
- **MUST** be named `main.py` (not `generate.py` or anything else)
- The backend looks specifically for `models/{model-name}/main.py`

### 2. Document Handling Pattern

**CRITICAL**: The backend provides a `doc` variable via `exec()`. **DO NOT** create a new document - use the provided one!

```python
#!/usr/bin/env python3
"""Your model description"""
import FreeCAD
import Part

# Backend provides 'doc' variable - we add objects to it
print(f"Using document: {doc.Name if 'doc' in dir() else 'Creating new for standalone'}")

# If running standalone (testing locally), create doc
if 'doc' not in dir():
    doc = FreeCAD.newDocument("MyModel")
    print("✓ Created new document (standalone mode)")
else:
    print("✓ Using provided document (backend mode)")

# Create your geometry
shape = Part.makeBox(100, 100, 100)

# Add to the provided document
obj = doc.addObject("Part::Feature", "MyObject")
obj.Shape = shape

# Recompute
doc.recompute()
print("SUCCESS: Model generation complete")
```

### 3. Available Variables in Execution Context

The backend executes your script with these variables available:
```python
{
    "FreeCAD": FreeCAD,      # FreeCAD module
    "doc": doc,               # Pre-created FreeCAD document
    "__name__": "__main__",   # Standard Python main
    "__file__": script_path   # Full path to your main.py
}
```

### 4. Using External Configuration Files

You can use `__file__` to load configuration from files like `input.json`:

```python
import os
import json

# Load parameters from input.json in same directory
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "input.json")

with open(input_file, 'r') as f:
    params = json.load(f)

# Use params in your model
width = params['width']
height = params['height']
```

**Example `input.json`:**
```json
{
  "width": 100,
  "height": 50,
  "thickness": 3
}
```

### 5. Success Indicator

**REQUIRED**: Print `"SUCCESS: Model generation complete"` at the end of your script. The backend looks for this message to determine if generation succeeded.

```python
print("SUCCESS: Model generation complete")
```

## CI/CD Workflow

### Automatic Triggers

The workflow triggers when you push changes to `models/**/*.py`:

1. **Checkout**: Fetches repository with `fetch-depth: 2` (for git diff)
2. **Detect Model**: Uses `git diff --name-only HEAD~1 HEAD` to find changed model
3. **Version**: Auto-increments as `1.0.{run_number}`
4. **Trigger Fargate**: Launches ECS task with environment variables:
   - `MODEL_NAME`: Detected from path (e.g., "keyboard")
   - `VERSION`: Auto-generated (e.g., "1.0.22")
   - `S3_BUCKET`: Target S3 bucket
   - `GITHUB_REPO_URL`: Clone URL
   - `COMMIT_SHA`: Git commit hash
   - `CHANGE_DESCRIPTION`: Commit message

### Manual Trigger

You can manually trigger via GitHub Actions UI:
```bash
gh workflow run "Generate CAD Model" -f model_name=demo -f version=1.0.0
```

Or via GitHub web UI: Actions → Generate CAD Model → Run workflow

### Backend Processing

The Fargate task executes these steps:

1. **Clone repository** at specific commit
2. **Execute FreeCAD script** (`models/{model}/main.py`)
3. **Generate multi-LOD STL files**:
   - `{ObjectName}_high.stl` (original resolution)
   - `{ObjectName}_medium.stl` (50% decimation)
   - `{ObjectName}_low.stl` (80% decimation)
4. **Create assembly manifest** (`assembly.json`)
5. **Upload to S3**: `s3://{bucket}/models/{model}/{version}/`
6. **Update status**: `status.json` with progress/errors

### Output Structure

```
s3://bucket/models/keyboard/1.0.22/
├── Key_1_high.stl
├── Key_1_medium.stl
├── Key_1_low.stl
├── Key_2_high.stl
├── ...
├── assembly.json          # Instance transforms and metadata
├── status.json            # Generation status
└── logs/
    └── generation.log     # Full execution logs
```

## Common Patterns

### Pattern 1: Simple Geometric Model

```python
#!/usr/bin/env python3
import FreeCAD
import Part

if 'doc' not in dir():
    doc = FreeCAD.newDocument("Simple")

# Create geometry
box = Part.makeBox(100, 50, 25)

# Add to document
obj = doc.addObject("Part::Feature", "Box")
obj.Shape = box

doc.recompute()
print("SUCCESS: Model generation complete")
```

### Pattern 2: Multiple Instances (Array)

```python
#!/usr/bin/env python3
import FreeCAD
import Part

if 'doc' not in dir():
    doc = FreeCAD.newDocument("Array")

# Create 9 repeated objects
for i in range(9):
    y_pos = i * 22  # 20mm spacing + 2mm gap
    box = Part.makeBox(18, 18, 5, FreeCAD.Vector(-9, y_pos, 0))

    obj = doc.addObject("Part::Feature", f"Item_{i+1}")
    obj.Shape = box

doc.recompute()
print("SUCCESS: Model generation complete")
```

### Pattern 3: Parametric with External Config

```python
#!/usr/bin/env python3
import FreeCAD
import Part
import json
import os

if 'doc' not in dir():
    doc = FreeCAD.newDocument("Parametric")

# Load config
script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, "input.json"), 'r') as f:
    params = json.load(f)

# Use parameters
outer = Part.makeBox(params['length'], params['width'], params['height'])
inner = Part.makeBox(
    params['length'] - 2*params['wall'],
    params['width'] - 2*params['wall'],
    params['height'] - params['wall'],
    FreeCAD.Vector(params['wall'], params['wall'], params['wall'])
)

hollow = outer.cut(inner)
obj = doc.addObject("Part::Feature", "HollowBox")
obj.Shape = hollow

doc.recompute()
print("SUCCESS: Model generation complete")
```

### Pattern 4: Complex Assembly

```python
#!/usr/bin/env python3
import FreeCAD
import Part

if 'doc' not in dir():
    doc = FreeCAD.newDocument("Assembly")

# Base
base = Part.makeBox(200, 200, 10)
base_obj = doc.addObject("Part::Feature", "Base")
base_obj.Shape = base

# Column
column = Part.makeCylinder(20, 150, FreeCAD.Vector(100, 100, 10))
column_obj = doc.addObject("Part::Feature", "Column")
column_obj.Shape = column

# Cap
cap = Part.makeSphere(30, FreeCAD.Vector(100, 100, 160))
cap_obj = doc.addObject("Part::Feature", "Cap")
cap_obj.Shape = cap

doc.recompute()
print("SUCCESS: Model generation complete")
```

## Testing Locally

### Option 1: FreeCAD GUI

```bash
freecad
# In FreeCAD console:
exec(open('/path/to/models/your-model/main.py').read())
```

### Option 2: FreeCAD CLI (Headless)

```bash
cd /path/to/cad-models
freecadcmd -c models/your-model/main.py
```

### Option 3: Simulating Backend Environment

```python
# test.py
import FreeCAD

doc = FreeCAD.newDocument("Test")
script_path = "/full/path/to/models/your-model/main.py"

with open(script_path, 'r') as f:
    script_content = f.read()

exec(script_content, {
    "FreeCAD": FreeCAD,
    "doc": doc,
    "__name__": "__main__",
    "__file__": script_path
})

print(f"Document has {len(doc.Objects)} objects")
```

## Troubleshooting

### Issue: `NameError: name '__file__' is not defined`

**Cause**: You're using `__file__` but the backend wasn't providing it in exec context.

**Fix**: This was fixed in commit `7b49e44`. Ensure you're using the latest backend Docker image.

**Workaround**: Use absolute paths or avoid `__file__` altogether.

### Issue: Workflow fails with "fatal: ambiguous argument 'HEAD~1'"

**Cause**: GitHub Actions checkout uses `fetch-depth: 1` by default, so `HEAD~1` doesn't exist.

**Fix**: Already fixed in `.github/workflows/generate-model.yml` with `fetch-depth: 2`.

### Issue: Workflow fails with "Invalid format" when using multiline commit messages

**Cause**: Multiline commit messages break GitHub Actions `echo "var=value"` output format.

**Fix**: Already fixed using heredoc syntax in workflow:
```yaml
{
  echo "change_desc<<EOF"
  echo "${{ github.event.head_commit.message }}"
  echo "EOF"
} >> $GITHUB_OUTPUT
```

### Issue: Model generates but doesn't appear in frontend

**Cause**: The `models/index.json` file in S3 doesn't list your model.

**Fix**: Manually update `models/index.json`:
```json
{
  "models": [
    {
      "name": "your-model",
      "displayName": "Your Model Name",
      "description": "Brief description",
      "versions": ["1.0.1", "1.0.2"]
    }
  ]
}
```

Upload to S3:
```bash
aws s3 cp index.json s3://cad-dev-models-aod1lux5/models/index.json --content-type "application/json"
```

### Issue: "Failed to execute FreeCAD script"

**Check CloudWatch Logs**:
```bash
aws logs tail /ecs/cad-dev-freecad --follow --since 10m
```

**Check Status File**:
```bash
aws s3 cp s3://cad-dev-models-aod1lux5/models/{model}/{version}/status.json -
```

**Common causes**:
- Syntax errors in your script
- Missing `print("SUCCESS: Model generation complete")`
- Using `FreeCAD.newDocument()` instead of provided `doc`
- Import errors (missing modules)

### Issue: STL files are empty or corrupted

**Cause**: Model has zero volume or invalid geometry.

**Debug**:
```python
# Add after creating shape
print(f"Shape volume: {shape.Volume}")
print(f"Shape is valid: {shape.isValid()}")
```

## Best Practices

1. **Always use the provided `doc`** - Don't create new documents
2. **Print progress messages** - Helps with debugging in CloudWatch logs
3. **Test locally first** - Use FreeCAD GUI or CLI before pushing
4. **Use meaningful object names** - Name your Part::Feature objects descriptively
5. **Keep scripts simple** - Complex logic can be hard to debug remotely
6. **Use `input.json` for parameters** - Easier to modify than hardcoded values
7. **Check shape validity** - Use `shape.isValid()` before adding to document
8. **End with SUCCESS message** - Required for backend to detect completion

## Monitoring Generation

### Check Status

```bash
# View status
aws s3 cp s3://cad-dev-models-aod1lux5/models/keyboard/1.0.22/status.json -

# List generated files
aws s3 ls s3://cad-dev-models-aod1lux5/models/keyboard/1.0.22/ --recursive

# View logs
aws s3 cp s3://cad-dev-models-aod1lux5/models/keyboard/1.0.22/logs/generation.log -
```

### Status JSON Structure

```json
{
  "status": "ready",           // or "started", "in-progress", "failed"
  "modelName": "keyboard",
  "version": "1.0.22",
  "timestamp": "2025-11-18T01:54:08.803573+00:00",
  "cdnUrl": "https://d2j2tqi3nk8zjp.cloudfront.net/models/keyboard/1.0.22/",
  "stage": "Complete",         // Current stage
  "progress": 100,             // Percentage (0-100)
  "error": null,               // Error message if failed
  "commitSha": "1ee3be4..."
}
```

### GitHub Actions Workflow Status

```bash
# List recent runs
gh run list --limit 5

# View specific run
gh run view <run-id>

# Watch running workflow
gh run watch
```

## Recent Fixes (November 2024)

### Fix 1: GitHub Actions Workflow (Commit: 1ee3be4)
- Added `fetch-depth: 2` to checkout step
- Fixed multiline commit message handling with heredoc

### Fix 2: Backend `__file__` Support (Commit: 7b49e44)
- Added `__file__` to exec context
- Enables loading external config files like `input.json`

### Fix 3: Script Naming Convention
- Changed from `generate.py` to `main.py` across all models
- Backend expects `models/{model}/main.py`

## Reference

- **Backend execution**: `/app/scripts/main.py` in Fargate container
- **Workflow**: `.github/workflows/generate-model.yml`
- **S3 bucket**: `cad-dev-models-aod1lux5`
- **CloudFront**: `https://d2j2tqi3nk8zjp.cloudfront.net`
- **ECS cluster**: `cad-dev-freecad-cluster`
- **Task definition**: `cad-dev-freecad-task`

For infrastructure changes or backend modifications, see the main CAD-AI repository.
