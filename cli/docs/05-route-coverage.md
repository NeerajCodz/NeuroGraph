# Backend Route Coverage

This matrix maps backend routes to CLI commands.

## 1. Auth routes

| Method | Backend path | CLI command |
| --- | --- | --- |
| POST | `/auth/register` | `auth register` |
| POST | `/auth/login` | `auth login` |
| POST | `/auth/refresh` | `auth refresh` |
| GET | `/auth/me` | `auth me` |
| POST | `/auth/logout` | `auth logout` |

## 2. Chat routes

| Method | Backend path | CLI command |
| --- | --- | --- |
| POST | `/chat/message` | `chat send`, `ask` |
| GET | `/chat/conversations` | `chat conversations` |
| GET | `/chat/conversations/{conversation_id}` | `chat conversation <id>` |
| DELETE | `/chat/conversations/{conversation_id}` | `chat delete <id>` |
| POST | `/chat/stream` | `chat stream` |

## 3. Conversation routes

| Method | Backend path | CLI command |
| --- | --- | --- |
| POST | `/conversations` | `conversations create` |
| GET | `/conversations` | `conversations list` |
| GET | `/conversations/{conversation_id}` | `conversations get <id>` |
| PATCH | `/conversations/{conversation_id}` | `conversations update <id>` |
| DELETE | `/conversations/{conversation_id}` | `conversations delete <id>` |
| GET | `/conversations/{conversation_id}/steps` | `conversations steps <id>` |

## 4. Memory routes

| Method | Backend path | CLI command |
| --- | --- | --- |
| POST | `/memory/remember` | `memory remember`, `remember` |
| POST | `/memory/recall` | `memory recall`, `recall` |
| GET | `/memory/search` | `memory search` |
| GET | `/memory/list` | `memory list` |
| GET | `/memory/count` | `memory count` |
| GET | `/memory/status` | `memory status` |
| GET | `/memory/{id}` | `memory get <id>` |
| DELETE | `/memory/{id}` | `memory delete <id>` |
| PATCH | `/memory/{id}/lock` | `memory lock <id>` |
| PATCH | `/memory/{id}/position` | `memory position <id>` |
| POST | `/memory/{id}/duplicate` | `memory duplicate <id>` |
| GET | `/memory/{id}/detail` | `memory detail <id>` |
| POST | `/memory/edges` | `memory edges create` |
| GET | `/memory/edges` | `memory edges list` |
| DELETE | `/memory/edges/{edge_id}` | `memory edges delete <id>` |

## 5. Workspace routes

| Method | Backend path | CLI command |
| --- | --- | --- |
| POST | `/workspaces` | `workspaces create` |
| GET | `/workspaces` | `workspaces list` |
| GET | `/workspaces/{workspace_id}` | `workspaces get <id>` |
| PATCH | `/workspaces/{workspace_id}` | `workspaces update <id>` |
| DELETE | `/workspaces/{workspace_id}` | `workspaces delete <id>` |
| POST | `/workspaces/{workspace_id}/join` | `workspaces join <id> --token` |
| GET | `/workspaces/{workspace_id}/members` | `workspaces members <id>` |
| POST | `/workspaces/{workspace_id}/regenerate-token` | `workspaces regenerate-token <id>` |

## 6. Graph routes

| Method | Backend path | CLI command |
| --- | --- | --- |
| POST | `/graph/entities` | `graph create-entity` |
| GET | `/graph/entities/{entity_id}` | `graph entity <id>` |
| GET | `/graph/entities` | `graph entities` |
| DELETE | `/graph/entities/{entity_id}` | `graph delete-entity <id>` |
| POST | `/graph/relationships` | `graph create-relationship` |
| GET | `/graph/relationships/{entity_id}` | `graph relationships <id>` |
| DELETE | `/graph/relationships/{relationship_id}` | `graph delete-relationship <id>` |
| GET | `/graph/visualize` | `graph visualize` |
| GET | `/graph/paths/{source_id}/{target_id}` | `graph paths <src> <dst>` |
| GET | `/graph/centrality` | `graph centrality` |

## 7. Models routes

| Method | Backend path | CLI command |
| --- | --- | --- |
| GET | `/models/providers` | `models providers` |
| GET | `/models/all` | `models all` |
| GET | `/models/provider/{provider_id}` | `models provider <id>` |
| GET | `/models/gemini` | `models gemini` |
| GET | `/models/nvidia` | `models nvidia` |
| GET | `/models/groq` | `models groq` |
| POST | `/models/test/{provider_id}/{model_id}` | `models test <provider> <model>` |
| GET | `/models/recommendations` | `models recommendations` |

## 8. Profile routes

| Method | Backend path | CLI command |
| --- | --- | --- |
| GET | `/profile/settings` | `profile settings` |
| PATCH | `/profile/user` | `profile update-user` |
| PATCH | `/profile/password` | `profile update-password` |
| PATCH | `/profile/settings` | `profile update-settings` |
| GET | `/profile/export` | `profile export` |

## 9. Integration routes

| Method | Backend path | CLI command |
| --- | --- | --- |
| GET | `/integrations/connections` | `integrations connections` |
| GET | `/integrations/connections/{connection_id}` | `integrations get <id>` |
| POST | `/integrations/connections` | `integrations create` |
| PATCH | `/integrations/connections/{connection_id}` | `integrations update <id>` |
| DELETE | `/integrations/connections/{connection_id}` | `integrations delete <id>` |
| POST | `/integrations/oauth/initiate` | `integrations oauth-initiate` |
| POST | `/integrations/oauth/callback` | `integrations oauth-callback` |
| GET | `/integrations/types` | `integrations types` |

## 10. MCP HTTP transport routes

| Method | Backend path | CLI command |
| --- | --- | --- |
| POST | `/mcp/invoke` | `mcp invoke` |
| GET | `/mcp/tools` | `mcp tools` |
| POST | `/mcp/invoke/api-key` | `mcp invoke-api-key` |

### Global MCP mode coverage (`--mcp`)

When `--mcp` is enabled, these commands route through `/mcp/invoke` with `tools/call`:

- `ask` → `neurograph_chat`
- `chat send`, `chat stream` → `neurograph_chat`
- `remember`, `memory remember` → `neurograph_remember`
- `recall`, `memory recall` → `neurograph_recall`
- `memory search` → `neurograph_search`
- `memory list` → `neurograph_list_memories`
- `memory count`, `memory status` → `neurograph_status`

## 11. Known backend limitations (not CLI gaps)

- `/integrations/oauth/initiate` and `/integrations/oauth/callback` currently return `501` in backend implementation.
- Some graph endpoints are marked TODO in backend internals; CLI commands still call the routes correctly.
