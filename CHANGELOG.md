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
