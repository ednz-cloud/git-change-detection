## v0.2.1 (2026-02-16)

### Fix

- **deps**: update dependency typer to >=0.23.1,<0.24.0

## v0.2.0 (2026-02-07)

### Feat

- **cli**: add validate command for checking metadata dependencies and schema validation

## v0.1.1 (2025-10-23)

### Fix

- do not indent json output as it can break stuff

## v0.1.0 (2025-09-12)

### Feat

- **schema**: add json schema for metadata files
- **core**: rename package to git-change-detection
- **output**: improve table format output

### Fix

- add dependency sanitizing to avoid graph resolution failures
- handle errors on import for fnmatch and os dynamic import in cli
- remove deprecated function in render_ouput for json dump
