# Security Boundary

This example is a sanitized repository package from a local Unreal Engine experiment.

## Preserved

- WorldForge-specific UE content assets.
- Offline bridge scripts and task schemas.
- Sanitized execution reports and checkpoints.
- Screenshots and handoff documentation.

## Removed Or Redacted

- private original project backup;
- UE `Saved/` and `Intermediate/` runtime caches;
- raw logs containing full external telemetry URLs;
- local user home paths;
- global Codex configuration paths;
- pycache and temporary compiled Python files.

## Runtime Guarantees

Opening this folder from Git does not:

- install software;
- change firewall rules;
- change registry keys;
- change system environment variables;
- start Remote Control;
- start WebSocket, HTTP, UDP, or TCP services;
- modify global Codex configuration.

Remote Control and MCP are deliberately left as documented next-stage work because the source run stopped before proving loopback-only binding.
