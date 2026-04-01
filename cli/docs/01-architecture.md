# NeuroGraph CLI Architecture

## 1. Goals

The Go CLI is designed to:

- Mirror frontend/backend feature behavior for command-line workflows
- Use backend APIs as source of truth for business logic
- Support both backend API routes and MCP HTTP transport routes
- Keep authentication/session state in a local config file

## 2. Package layout

```
cli/
  cmd/
    neurograph/
      main.go
  internal/
    api/
      client.go
    commands/
      *.go
    config/
      config.go
    output/
      output.go
```

## 3. Responsibilities by package

### 3.1 `cmd/neurograph/main.go`

- CLI entrypoint
- Executes root Cobra command

### 3.2 `internal/commands`

- Command tree and flags
- Request payload/query construction
- Runtime config loading and login checks
- Output rendering for human and JSON modes

### 3.3 `internal/api/client.go`

- HTTP transport abstraction for backend calls
- JWT auth header injection where required
- Form login flow (`/auth/login`)
- JSON-RPC style MCP invoke calls:
  - `POST /mcp/invoke` (JWT auth)
  - `POST /mcp/invoke/api-key` (API key)

### 3.4 `internal/config/config.go`

- Persistent CLI settings and token storage
- Default values and config path resolution
- Login state evaluation and token expiration handling

### 3.5 `internal/output/output.go`

- Shared console output helpers
- Table rows, key-value blocks, and JSON rendering

## 4. Layer mapping model

The backend has slight route differences for layer naming:

- Memory/graph workflows use `tenant` for workspace scope
- Chat workflows use `workspace`

The CLI handles this with helper functions:

- `mapLayer(...)` for memory/graph style payloads (`workspace -> tenant`)
- `mapChatLayer(...)` for chat payloads (`tenant -> workspace`)

This keeps command behavior aligned with backend contracts while preserving user-friendly `workspace` semantics.

## 5. Authentication and runtime model

Runtime helper flow:

1. `loadRuntime()` loads config and constructs API client
2. `requireLogin()` checks token presence and expiration (`IsLoggedIn()`)
3. Commands call API client methods with built payloads
4. Token updates are persisted via `saveRuntime(...)`

## 6. Command surface

Root command groups:

- `auth`
- `config`
- `memory`
- `chat`
- `conversations`
- `workspaces`
- `graph`
- `models`
- `integrations`
- `profile`
- `mcp`
- quick aliases: `ask`, `remember`, `recall`
