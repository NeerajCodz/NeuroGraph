# NeuroGraph Go CLI Documentation

## 1. Status and implementation results

This directory documents the Go rewrite of the NeuroGraph CLI in `cli/`.

Current implementation status:

- Complete Go CLI foundation (`cmd`, `internal`, config, API client, output helpers)
- Command groups implemented: `auth`, `config`, `memory`, `chat`, `conversations`, `workspaces`, `graph`, `models`, `integrations`, `profile`, `mcp`
- Quick aliases implemented: `ask`, `remember`, `recall`
- Backend and MCP integration implemented (JWT auth and MCP API key flow)
- Tests added for config and API client behavior

Validation summary:

- `go build ./cmd/neurograph` passes
- `go test ./internal/api -count=1` passes
- Full `go test ./...` is environment-blocked in this runtime by OS Application Control for generated test executables

## 2. Documentation index

- `01-architecture.md`  
  Architecture, package layout, and design decisions.

- `02-setup-and-quickstart.md`  
  Build, run, login/logout, and common command flows.

- `03-configuration.md`  
  Config file schema, keys, defaults, and examples.

- `04-command-reference.md`  
  Structured command reference by group.

- `05-route-coverage.md`  
  Backend route to CLI command coverage mapping.

- `06-testing-and-validation.md`  
  Test suite details, executed validation, and local verification steps.

## 3. Important compatibility notes

- The CLI is backend-driven and does not replace backend or MCP services.
- Memory and graph layers on backend use `tenant` for workspace scope.
- Chat routes expect `workspace` layer; the CLI maps defaults appropriately.
- Integration OAuth routes exist in CLI, but backend currently returns `501` for initiate/callback implementation status.
