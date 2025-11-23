# CAD Models Repository - Agent Instructions

## Purpose

This repository contains FreeCAD Python scripts that generate parametric 3D models. When you push changes to `models/**/*.py`, GitHub Actions automatically triggers model generation via an SQS-based job queue system.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Push to main  │────>│  GitHub Actions │────>│   SQS Queue     │
│   (cad-models)  │     │   Workflow      │     │  (Job Queue)    │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                        ┌────────────────────────────────┘
                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Fargate Task  │────>│  FreeCAD Script │────>│   S3 Upload     │
│  (Warm Pool)    │     │   Execution     │     │  (STL + JSON)   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                        ┌────────────────────────────────┘
                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   CloudFront    │     │  SNS Topic      │     │   Screenshots   │
│   CDN Delivery  │     │  (Job Complete) │     │  (Playwright)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Key Infrastructure Components

| Component | Resource | Purpose |
|-----------|----------|---------|
| **SQS Queue** | `cad-dev-job-queue` | Job submission queue |
| **SNS Topic** | `cad-dev-job-complete` | Job completion notifications |
| **S3 Bucket** | `cad-dev-models-aod1lux5` | Model storage |
| **CloudFront** | `d2j2tqi3nk8zjp.cloudfront.net` | CDN for models |
| **ECS Cluster** | `cad-dev-freecad-cluster` | Fargate execution |
| **Frontend** | `d261sntojya397.cloudfront.net` | 3D viewer |

## Workflow: Submitting Jobs

### Automatic (Push to main)

When you push changes to `models/**/*.py`:

1. GitHub Actions detects changed model via `git diff`
2. Workflow sends job message to SQS queue
3. Workflow starts Fargate task if none running (warm pool)
4. Workflow polls S3 `status.json` for completion
5. On success, displays screenshots in job summary

### Manual Trigger

```bash
# Via GitHub CLI
gh workflow run generate-model.yml -f model_name=demo -f version=1.0.0

# Via GitHub web UI: Actions -> Generate CAD Model -> Run workflow
```

## Waiting for Job Completion

### Method 1: Poll S3 Status (Recommended for Scripts)

```bash
# Poll status.json until ready or failed
MODEL="your-model"
VERSION="1.0.0"
BUCKET="cad-dev-models-aod1lux5"

while true; do
  STATUS=$(aws s3 cp "s3://${BUCKET}/models/${MODEL}/${VERSION}/status.json" - 2>/dev/null)
  CURRENT=$(echo "$STATUS" | jq -r '.status // "pending"')

  echo "Status: $CURRENT"

  if [ "$CURRENT" == "ready" ]; then
    echo "Model generation complete!"
    break
  elif [ "$CURRENT" == "failed" ]; then
    echo "Model generation failed: $(echo "$STATUS" | jq -r '.error')"
    exit 1
  fi

  sleep 10
done
```

### Method 2: SNS Subscription (Recommended for Real-time Updates)

The SNS topic `cad-dev-job-complete` publishes messages when jobs finish:

**Message Format:**
```json
{
  "modelName": "keyboard",
  "version": "1.0.56",
  "status": "ready",
  "timestamp": "2025-11-23T05:46:51.588050+00:00",
  "s3Prefix": "models/keyboard/1.0.56/",
  "cdnUrl": "https://d2j2tqi3nk8zjp.cloudfront.net/models/keyboard/1.0.56/",
  "screenshotUrls": [
    "https://d2j2tqi3nk8zjp.cloudfront.net/screenshots/keyboard/1.0.56/isometric.png"
  ]
}
```

**Subscribe via email (for testing):**
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:705123537290:cad-dev-job-complete \
  --protocol email \
  --notification-endpoint your-email@example.com
```

**Subscribe via HTTP endpoint:**
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:705123537290:cad-dev-job-complete \
  --protocol https \
  --notification-endpoint https://your-webhook.com/cad-updates
```

### Method 3: Watch GitHub Workflow

```bash
# Watch the running workflow
gh run watch

# Or list recent runs
gh run list --limit 5
```

## Status JSON Structure

The `status.json` file tracks generation progress:

```json
{
  "status": "ready",           // "started" | "in-progress" | "ready" | "failed"
  "modelName": "keyboard",
  "version": "1.0.56",
  "timestamp": "2025-11-23T05:46:51.588050+00:00",
  "cdnUrl": "https://d2j2tqi3nk8zjp.cloudfront.net/models/keyboard/1.0.56/",
  "stage": "Complete",         // Current processing stage
  "progress": 100,             // 0-100 percentage
  "error": null,               // Error message if failed
  "commitSha": "65ecdfa..."
}
```

**Progress Stages:**
| Stage | Progress | Description |
|-------|----------|-------------|
| Starting | 0% | Job received |
| Cloning repository | 10% | Fetching code from GitHub |
| Executing FreeCAD | 30% | Running your main.py |
| Generating STL files | 50% | Creating multi-LOD meshes |
| Creating assembly manifest | 70% | Building assembly.json |
| Uploading to S3 | 85% | Uploading files to S3 |
| Capturing screenshots | 90% | Taking model screenshots |
| Complete | 100% | Ready for viewing |

## Screenshots

The backend captures isometric screenshots automatically using Playwright:

- **Default view**: `screenshots/{model}/{version}/isometric.png`
- **Custom views**: Configure via `screenshots.json` in your model folder

**Example `screenshots.json`:**
```json
{
  "defaults": {
    "orthographic": true,
    "background": "1a0033",
    "wireframe": false
  },
  "views": [
    {
      "name": "isometric",
      "camera": { "position": [100, 100, 100], "target": [0, 0, 0] },
      "zoom": 1.0
    },
    {
      "name": "front",
      "camera": { "position": [0, -200, 0], "target": [0, 0, 0] }
    },
    {
      "name": "top",
      "camera": { "position": [0, 0, 200], "target": [0, 0, 0] }
    }
  ]
}
```

**Screenshot URLs:**
```
https://d2j2tqi3nk8zjp.cloudfront.net/screenshots/{model}/{version}/isometric.png
```

## Repository Structure

```
models/
├── demo/              # Simple cube demonstration
│   └── main.py       # FreeCAD script (required)
├── parametric-box/   # Hollow box with configurable dimensions
│   ├── main.py
│   └── input.json    # Optional: external configuration
├── keyboard/         # Parametric keyboard with 9 keycaps
│   ├── main.py
│   ├── input.json
│   └── screenshots.json  # Optional: screenshot configuration
└── your-model/       # Add new models here
    ├── main.py       # REQUIRED: Must be named main.py
    ├── input.json    # OPTIONAL: External parameters
    └── screenshots.json  # OPTIONAL: Custom screenshot views
```

## FreeCAD Script Requirements

### 1. File Naming
- **MUST** be named `main.py`
- Backend looks for `models/{model-name}/main.py`

### 2. Document Handling

**CRITICAL**: Use the provided `doc` variable - don't create a new document!

```python
#!/usr/bin/env python3
"""Your model description"""
import FreeCAD
import Part

# Backend provides 'doc' variable via exec()
if 'doc' not in dir():
    doc = FreeCAD.newDocument("MyModel")
    print("Created new document (standalone mode)")
else:
    print("Using provided document (backend mode)")

# Create your geometry
shape = Part.makeBox(100, 100, 100)

# Add to document
obj = doc.addObject("Part::Feature", "MyObject")
obj.Shape = shape

doc.recompute()
print("SUCCESS: Model generation complete")
```

### 3. Success Indicator

**REQUIRED**: Print `"SUCCESS: Model generation complete"` at the end of your script.

### 4. Using External Config

```python
import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, "input.json"), 'r') as f:
    params = json.load(f)

width = params['width']
```

## Output Files

After successful generation:

```
s3://cad-dev-models-aod1lux5/
├── models/{model}/{version}/
│   ├── {ObjectName}_high.stl    # Full resolution
│   ├── {ObjectName}_medium.stl  # 50% decimation
│   ├── {ObjectName}_low.stl     # 80% decimation
│   ├── assembly.json            # Instance transforms
│   ├── status.json              # Generation status
│   └── logs/
│       └── queue_worker.log     # Execution logs
└── screenshots/{model}/{version}/
    └── isometric.png            # Model screenshot
```

## Monitoring & Debugging

### Check Generation Status
```bash
aws s3 cp s3://cad-dev-models-aod1lux5/models/keyboard/1.0.56/status.json -
```

### List Generated Files
```bash
aws s3 ls s3://cad-dev-models-aod1lux5/models/keyboard/1.0.56/ --recursive
```

### View Execution Logs
```bash
aws s3 cp s3://cad-dev-models-aod1lux5/models/keyboard/1.0.56/logs/queue_worker.log -
```

### View CloudWatch Logs (Real-time)
```bash
aws logs tail /ecs/cad-dev-freecad --follow --since 10m
```

### View in 3D Viewer
```
https://d261sntojya397.cloudfront.net/viewer?model=keyboard&version=1.0.56
```

## Warm Pool Behavior

The Fargate container uses a "warm pool" pattern:

1. **First job**: Cold start ~2-3 minutes (container provisioning)
2. **Subsequent jobs**: ~10-15 seconds (container reuses)
3. **Idle timeout**: Container exits after 30 minutes of no jobs
4. **Auto-scale**: New container starts when job arrives

This means:
- First model after inactivity: slower (~3 min total)
- Rapid iteration: very fast (~15 sec per model)

## Common Issues

### Job stuck at "pending"
```bash
# Check if Fargate task is running
aws ecs list-tasks --cluster cad-dev-freecad-cluster --desired-status RUNNING

# If no tasks, manually start one (workflow does this automatically)
aws ecs run-task --cluster cad-dev-freecad-cluster \
  --task-definition cad-dev-freecad-task \
  --launch-type FARGATE \
  --network-configuration "..."
```

### "Failed to execute FreeCAD script"
1. Check logs: `aws s3 cp s3://.../logs/queue_worker.log -`
2. Common causes:
   - Syntax errors in script
   - Missing `print("SUCCESS: Model generation complete")`
   - Using `FreeCAD.newDocument()` instead of provided `doc`

### Screenshots not appearing
1. Verify status.json shows "ready" status
2. Check screenshot URL: `https://d2j2tqi3nk8zjp.cloudfront.net/screenshots/{model}/{version}/isometric.png`
3. Check logs for Playwright errors

## GitHub Secrets Required

The workflow uses these secrets (already configured):

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `AWS_REGION` | `us-east-1` |
| `S3_BUCKET` | `cad-dev-models-aod1lux5` |
| `SQS_QUEUE_URL` | SQS job queue URL |
| `ECS_CLUSTER_NAME` | `cad-dev-freecad-cluster` |
| `ECS_TASK_DEFINITION` | `cad-dev-freecad-task` |
| `ECS_SUBNET_IDS` | VPC subnet IDs |
| `ECS_SECURITY_GROUP_ID` | Security group ID |
| `CLOUDFRONT_URL` | `https://d2j2tqi3nk8zjp.cloudfront.net` |
| `FRONTEND_URL` | `https://d261sntojya397.cloudfront.net` |

## Quick Reference

```bash
# Trigger manual generation
gh workflow run generate-model.yml -f model_name=demo -f version=1.0.0

# Watch workflow progress
gh run watch

# Check model status
aws s3 cp s3://cad-dev-models-aod1lux5/models/demo/1.0.0/status.json -

# View model in browser
open "https://d261sntojya397.cloudfront.net/viewer?model=demo&version=1.0.0"

# View screenshot
open "https://d2j2tqi3nk8zjp.cloudfront.net/screenshots/demo/1.0.0/isometric.png"

# View logs
aws logs tail /ecs/cad-dev-freecad --since 10m
```

## Reference URLs

| Resource | URL |
|----------|-----|
| 3D Viewer | `https://d261sntojya397.cloudfront.net` |
| Models CDN | `https://d2j2tqi3nk8zjp.cloudfront.net` |
| Model URL pattern | `/models/{model}/{version}/` |
| Screenshot URL pattern | `/screenshots/{model}/{version}/{view}.png` |

For infrastructure changes or backend modifications, see the main CAD-AI repository.
