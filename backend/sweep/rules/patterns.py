"""Ce qui reconnaît un agent, un serveur MCP ou un serveur de développement."""

import re
from datetime import timedelta

AGENT_PROGRAMS = frozenset(
    {"claude", "agy", "gemini", "codex", "cursor-agent", "aider", "opencode"}
)
# Lancés en `node …/claude` par certaines installations : le nom du process est alors `node`.
AGENT_SCRIPT = re.compile(r"(^|[/\\])(claude|gemini|codex|opencode)(\.js|\.mjs)?$")
# Agents qui tournent sans terminal par conception : jamais « oubliés » faute de terminal.
HEADLESS_ARGUMENTS = frozenset(
    {"-p", "--print", "--headless", "remote-control", "serve", "mcp", "daemon", "exec"}
)
# Cherché dans le programme et ses premiers arguments, sur le dernier segment d'un chemin ou d'un
# paquet (`@playwright/mcp@0.0.83`, `.bin/context7-mcp`) : un script passé par `-c` ou un titre de
# process (`postgres: annski_mcp_lecture …`) contient des espaces et n'est jamais retenu.
MCP_NAME = re.compile(r"^([\w.]+-)?mcp(-[\w.-]+)?(@[\w.-]+)?$|modelcontextprotocol", re.IGNORECASE)
MCP_ARGUMENTS_SCANNED = 4
MCP_STDIO_PROGRAMS = frozenset({"toolbox"})
STDIO_FLAG = "--stdio"
# Intermédiaires entre un agent et son serveur MCP ; jamais `bash`, le shell de l'utilisateur.
LAUNCHER_PROGRAMS = frozenset({"npm", "npx", "uvx", "pnpm", "node", "sh", "dash"})
DEV_SERVER_COMMAND = re.compile(
    r"(nuxt(\.mjs)? dev|next dev|astro dev|\bvite\b|manage\.py runserver|uvicorn .*--reload"
    r"|streamlit run|marimo edit|webpack serve)"
)
# Arguments qui nomment la conversation reprise : deux agents sur la même se marchent dessus.
SESSION_FLAGS = frozenset({"--conversation", "--resume", "-r", "--session-id"})

IDLE_AGENT_AGE = timedelta(hours=3)
IDLE_CPU_PERCENT = 1.0
