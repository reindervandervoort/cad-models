# Claude Code Configuration

This directory contains agents and scripts for working with the CAD models repository.

## Directory Structure

```
.claude/
├── agents/
│   └── review-model.md      # Agent for reviewing model generation results
├── scripts/
│   ├── view_model.js        # Playwright script for viewing models
│   └── package.json         # npm dependencies (playwright)
├── credentials.txt          # Stored credentials for model viewer
└── README.md               # This file
```

## Agents

### review-model

**Purpose**: Automated review of CAD model generation results

**Usage**:
```
"Use the review-model agent to review the latest keyboard build"
```

**What it does**:
1. Determines the latest GitHub Actions run number
2. Polls the backend every 10 seconds until model is ready
3. Uses Playwright to view the model in the 3D viewer
4. Takes a screenshot and analyzes the results
5. Reports back with findings

**Self-sufficient**: The agent has all information needed to operate independently.

## Scripts

### view_model.js

Playwright script that:
- Logs into the model viewer with stored credentials
- Navigates to the specified model/version
- Waits for 3D rendering to complete
- Takes a screenshot
- Extracts scene information

**Usage**:
```bash
node .claude/scripts/view_model.js <model> <version>
```

**Example**:
```bash
node .claude/scripts/view_model.js keyboard 1.1.144
```

**Setup** (first time only):
```bash
cd .claude/scripts
npm install
npx playwright install chromium
```

## Credentials

The `credentials.txt` file stores authentication information for the model viewer:
- Email: reindervandervoort@gmail.com
- Password: CadAi2025!

This allows agents and scripts to access the viewer without manual login.

## Integration with Main Workflow

The review agent is integrated into the main CAD modeling workflow:

1. **Make changes** to a model's `main.py`
2. **Push to main** (triggers GitHub Actions)
3. **Use review agent** to wait for and view results
4. **Iterate** based on feedback

See `AGENT.md` in the repository root for complete workflow documentation.
