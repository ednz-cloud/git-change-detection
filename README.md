# git-change-detection

Dependency-aware change detection for Git repositories.
Detects changed files between commits, resolves dependent nodes, and calculates deployment stages based on user-defined metadata.

This tool was initially developed to detect changes in ansible environments, and trigger playbooks in dependency order.

---

## Features

- Detect changed files between two commits.
- Resolve dependent nodes using triggers and dependencies.
- Handle blacklists to ignore specific nodes.
- Output results in **table** or **JSON** format.
- Easily integrates into CI/CD pipelines.

---

## Installation

```bash
pip install git-change-detection
```

or for development:

```bash
git clone https://github.com/ednz-cloud/git-change-detection.git
cd git-change-detection
poetry install
```

---

## Usage

```bash
git-change-detection <commit1> <commit2> [--repo <repo_path>] --metadata <metadata_file> [--json]
```

Example:

```bash
git-change-detection a8471715 2ee06c3e --repo ~/projects/infrastructure --metadata ~/projects/infrastructure/.metadata.yml --metadata ~/projects/infrastructure/custom1/.metadata.yml
```

---

## Metadata File Format

Define nodes and their triggers:

```yaml
---
playbooks/bootstrap.yml:
  depends_on: []
  triggers:
    ansible/playbooks:
      - bootstrap.yml
      - tasks/crowdsec.yml
    sops:
      - keypair.secret.json

playbooks/k3s_cluster.yml:
  depends_on:
    - playbooks/bootstrap.yml
  triggers:
    ansible/playbooks:
      - k3s_cluster.yml
```

* **triggers**: Maps paths or glob patterns to nodes.
* **depends_on**: Lists other nodes that must run before this one.
* **blacklist**: Optional list of nodes to ignore.

Example blacklist:

```yaml
blacklist:
  - playbooks/netbird_controller.yml
```

You can specify multiple metadata sources.
All sources will be deep merged together prior to calculating the dependency graph.

---

## CLI Output

### Table Example

```
Changed files
  ansible/install_docker.yml
  ansible/netbird_router.yml
  ansible/netbird_routers.yml

Triggered Nodes
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Node                          ┃ File                        ┃ Pattern                     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ playbooks/netbird_routers.yml │ vars/install_docker.yml     │ vars/*                      │
│                               │ vars/netbird_router.yml     │ ansible/netbird_routers.yml │
│                               │ ansible/netbird_routers.yml │                             │
└───────────────────────────────┴─────────────────────────────┴─────────────────────────────┘

Deployment Stages
  Stage 1: playbooks/netbird_routers.yml
```

### JSON Example

```json
{
  "playbooks/netbird_routers.yml": {
    "name": "playbooks/netbird_routers.yml",
    "depends_on": [],
    "triggered": true,
    "triggers": {
      "vars": [
        "*"
      ],
      "ansible": [
        "netbird_routers.yml"
      ]
    },
    "triggered_by": [
      {
        "file": "vars/install_docker.yml",
        "pattern": "vars/*"
      },
      {
        "file": "vars/netbird_router.yml",
        "pattern": "vars/*"
      },
      {
        "file": "ansible/netbird_routers.yml",
        "pattern": "ansible/netbird_routers.yml"
      }
    ],
    "stage": 1
  }
}
```

* Shows **changed files**, **triggered nodes**, and **deployment stages**.
* Blacklisted nodes will not appear even if triggered.

---

## CI/CD Integration

Automatically detect changes and trigger dependent workflows:

```yaml
- name: Detect changed nodes
  run: git-change-detection <commit1> <commit2> --repo ~/projects/infrastructure --metadata .metadata.yml --json
```

---

## Contributing

PRs and issues are welcome!
Follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## License

MIT
