# Command Reference

This reference is grouped by root command.

## 1. `auth`

- `auth register --email --password [--full-name]`
- `auth login --email --password`
- `auth refresh`
- `auth logout`
- `auth me [--json]`

## 2. `config`

- `config show [--json]`
- `config set <key> <value>`
- `config get <key>`
- `config reset`
- `config path`

## 3. `memory`

- `memory remember <content> [--layer] [--workspace-id]`
- `memory recall <query> [--layers] [--workspace-id] [--limit] [--min-confidence] [--json]`
- `memory search <query> [--layers] [--workspace-id] [--limit] [--json]`
- `memory list [--layer] [--workspace-id] [--limit] [--offset] [--json]`
- `memory count [--workspace-id] [--json]`
- `memory status [--workspace-id] [--json]`
- `memory get <id> [--json]`
- `memory delete <id>`
- `memory lock <id>`
- `memory position <id> --x --y`
- `memory duplicate <id> [--json]`
- `memory detail <id> [--json]`
- `memory edges create <source_id> <target_id> [--reason] [--confidence]`
- `memory edges list [--layer] [--workspace-id] [--json]`
- `memory edges delete <edge_id>`

## 4. `chat`

- `chat send <message> [--conversation-id] [--workspace-id] [--layer] [--global] [--provider] [--model] [--agents-enabled] [--json]`
- `chat conversations [--workspace-id] [--limit] [--offset] [--json]`
- `chat conversation <conversation_id> [--json]`
- `chat delete <conversation_id>`
- `chat stream <message> [--workspace-id] [--layer] [--global] [--provider] [--model] [--agents-enabled] [--json]`

## 5. `conversations`

- `conversations create [--workspace-id] [--title] [--json]`
- `conversations list [--workspace-id] [--include-archived] [--limit] [--offset] [--json]`
- `conversations get <conversation_id> [--include-messages] [--message-limit] [--json]`
- `conversations update <conversation_id> [--title] [--pinned] [--archived] [--json]`
- `conversations delete <conversation_id>`
- `conversations steps <conversation_id> [--message-id] [--json]`

## 6. `workspaces`

- `workspaces create --name [--description] [--public] [--memory-enabled] [--default-provider] [--default-model] [--json]`
- `workspaces list [--include-shared] [--json]`
- `workspaces get <workspace_id> [--json]`
- `workspaces update <workspace_id> [--name] [--description] [--public] [--memory-enabled] [--default-provider] [--default-model] [--json]`
- `workspaces delete <workspace_id>`
- `workspaces join <workspace_id> --token`
- `workspaces members <workspace_id> [--json]`
- `workspaces regenerate-token <workspace_id> [--json]`
- `workspaces use <workspace_id>`
- `workspaces current`

## 7. `graph`

- `graph entities [--query] [--types] [--layer] [--limit] [--json]`
- `graph entity <entity_id> [--json]`
- `graph create-entity --name --type [--layer] [--json]`
- `graph delete-entity <entity_id>`
- `graph relationships <entity_id> [--direction] [--types] [--json]`
- `graph create-relationship --source-id --target-id --type [--reason] [--confidence] [--json]`
- `graph delete-relationship <relationship_id>`
- `graph visualize [--center-entity] [--depth] [--max-nodes] [--json]`
- `graph paths <source_id> <target_id> [--max-depth] [--json]`
- `graph centrality [--entity-ids] [--json]`

## 8. `models`

- `models providers [--json]`
- `models all [--json]`
- `models provider <provider_id> [--json]`
- `models gemini [--json]`
- `models groq [--json]`
- `models nvidia [--json]`
- `models test <provider_id> <model_id> [--json]`
- `models recommendations [--json]`

## 9. `integrations`

- `integrations connections [--tenant-id] [--integration-type] [--scope] [--enabled-only] [--json]`
- `integrations get <connection_id> [--json]`
- `integrations create --integration-type [--scope] [--tenant-id] [--name] [--enabled] [--json]`
- `integrations update <connection_id> [--name] [--enabled] [--json]`
- `integrations delete <connection_id>`
- `integrations types [--json]`
- `integrations oauth-initiate --integration-type --redirect-uri [--scope] [--tenant-id] [--json]`
- `integrations oauth-callback --code --state [--json]`

## 10. `profile`

- `profile settings [--json]`
- `profile update-user --full-name [--json]`
- `profile update-password --current-password --new-password --confirm-password [--json]`
- `profile update-settings [--default-provider] [--default-model] [--default-memory-layer] [--agents-enabled] [--theme] [--compact-mode] [--show-confidence] [--show-reasoning] [--json]`
- `profile export [--json]`

## 11. `mcp`

- `mcp tools [--json]`
- `mcp invoke --tool [--query] [--content] [--layer] [--workspace-id] [--response-format] [--max-results] [--json]`
- `mcp invoke-api-key --tool [--query] [--content] [--layer] [--workspace-id] [--json]`

## 12. Quick aliases

- `ask <message> [--provider] [--model] [--global]`
- `remember <content> [--layer]`
- `recall <query> [--limit]`
