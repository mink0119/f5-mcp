[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/czirakim-f5-mcp-server-badge.png)](https://mseep.ai/app/czirakim-f5-mcp-server)

# F5 MCP Server
[![smithery badge](https://smithery.ai/badge/@czirakim/F5.MCP.server)](https://smithery.ai/server/@czirakim/F5.MCP.server)

<img width="724" alt="image" src="https://github.com/user-attachments/assets/6bffb811-3e89-49fb-9d31-c7173afc9adc" />

This project is a **MCP (Model Context Protocol) server** that talks to F5 devices via the **iControl REST API**. It exposes tools for managing F5 TMOS (BIG-IP) objects (virtual servers, pools, profiles, etc.) and for applying **L4 standard settings** (DB and profiles) with optional before/after verification.

**For new users:** Configure `.env` (see [Configuration](#configuration-env)), point your MCP client (e.g. Claude Desktop) at this server, then see [Documentation (Guides)](#documentation-guides) for the process flow and tool usage.

## Features

- **Tool-Based API**: The project defines tools (`list_tool`, `create_tool`, `update_tool`, `delete_tool`, `apply_l4_standard_db_tool`, `apply_l4_standard_profiles_tool`, etc.) that encapsulate operations on F5 devices.
- **REST API Integration**: Uses Python's `requests` library to communicate with F5 devices via the iControl REST API.
- **Environment Configuration**: Sensitive information like IP addresses and authorization strings are managed through environment variables loaded from a `.env` file.
- **Extensibility**: Modular design allows additional tools or functionalities to be added easily.
- **Transport Support**: The server runs using the `stdio` transport, making it compatible with various client integrations.
- **Dockerfile**: If you want to run this as a Docker container

## Configuration (.env)

The server reads configuration from environment variables (optionally from the project `.env` file).

A generic helper chooses which device API to use based on the
``F5_ENDPOINT_TYPE`` environment variable.  Valid values are ``TMOS`` (the
default) and ``F5OS``; if the variable is not present the MCP will connect
using the TMOS/iControl REST settings.

For convenience you may also set the _generic_ variables ``F5_HOST``,
``F5_PORT``, ``F5_AUTH_BASIC_B64``, ``F5_VERIFY_TLS`` and
``F5_TIMEOUT_SECONDS``.  If ``F5_HOST`` is defined those values override the
per‑endpoint variables regardless of the selected type.


### Endpoints

This project can be configured with **two separate endpoints**; the active
one is selected by ``F5_ENDPOINT_TYPE`` (see above).

- **TMOS (iControl REST)**: used by the current LTM tools (`/mgmt/tm/...`)
- **F5OS (RESTCONF)**: reserved for future RESTCONF tools (`/restconf/...`)

### Required (TMOS)

- `TMOS_HOST`
- `TMOS_AUTH_BASIC_B64` (Base64 of `username:password`, without the `Basic ` prefix)

Legacy keys (still supported for TMOS):

- `IP_ADDRESS` (same as `TMOS_HOST`)
- `Authorization_string` (same as `TMOS_AUTH_BASIC_B64`)

### Per-request connection (no redeploy for new devices or password change)

Every TMOS tool accepts **optional** `tmos_host`, `tmos_port`, `tmos_username`, `tmos_password`. If you pass them, **that request only** uses that connection (env is ignored for that call). So you can:

- **After changing the admin password**: call the next tool (e.g. root password change) with `tmos_username="admin"`, `tmos_password="<new password>"` to avoid 401 without changing `.env` or redeploying.
- **Multiple devices**: pass different `tmos_host` and credentials per request. No need to change code or env when adding a new device; the client (or AI) passes the target device and credentials each time.

### Optional (TMOS)

- `TMOS_PORT` (default: `443`)
- `TMOS_VERIFY_TLS` (default: `false`)
- `TMOS_TIMEOUT_SECONDS` (default: `20`)

### Required (F5OS)

- `F5OS_HOST`
- `F5OS_AUTH_BASIC_B64`

### Optional (F5OS)

- `F5OS_PORT` (default: `8888`)
- `F5OS_VERIFY_TLS` (default: `false`)
- `F5OS_TIMEOUT_SECONDS` (default: `20`)

Example `.env`:

```bash
TMOS_HOST=192.168.47.55
TMOS_PORT=443
TMOS_AUTH_BASIC_B64=YWRtaW46YWRtaW4=
TMOS_VERIFY_TLS=false
TMOS_TIMEOUT_SECONDS=20

F5OS_HOST=192.168.45.246
F5OS_PORT=8888
F5OS_AUTH_BASIC_B64=YWRtaW46YWRtaW4=
F5OS_VERIFY_TLS=false
F5OS_TIMEOUT_SECONDS=20
```

## F5OS Standard Configuration

For **F5OS deployments**, there is a mandatory initialization step for backup encryption:

### Primary-Key Setup (Required)

The `f5os_init_aaa_primary_key_tool` sets the encryption key used for backup and configuration data protection.

**Step 1: Check current state**
```
f5os_check_aaa_primary_key_state_tool()
```

**Step 2: Set primary-key** (if not already set)
```
f5os_init_aaa_primary_key_tool(passphrase="YourPassphrase", salt="YourSalt")
```

**Step 3: Verify setup**
```
f5os_check_aaa_primary_key_state_tool()
```

**Requirements:**
- passphrase: 6-255 characters
- salt: 6-255 characters
- Store these values securely; they are needed for backup recovery

**CLI equivalent:**
```bash
appliance-1# show system aaa primary-key state status
appliance-1# config
appliance-1(config)# system aaa primary-key set passphrase
```

## TMOS: Basic Settings & L4 Standard (Templates)

For **TMOS (BIG-IP)** there are two template-style flows:

1. **Basic settings (기본 설정)** — "기본 설정 해줘"  
   `apply_basic_settings_tool(hostname=..., nameservers=..., ntp_servers=..., timezone=..., admin_password=..., root_password=..., syslog options...)`  
   Applies hostname, admin/root password, DNS, NTP (+ timezone), and syslog in one go. Only provided parameters are applied.

2. **L4 standard (L4 표준 설정)** — "L4 표준 설정 해줘" Use the **verification tools** first if you need an accurate before/after comparison.

### Basic Settings Tool

| Tool | Purpose |
|------|--------|
| `apply_basic_settings_tool(...)` | Apply device basic setup: hostname, admin/root password, DNS, NTP (+ timezone), syslog. Only provided parameters are applied. |

### L4 Standard Tools

| Tool | Purpose |
|------|--------|
| `get_l4_standard_db_state_tool()` | Read **current device values** for sys_db (8 items) and ltm connection (3 items). Use this as **Before** when comparing. |
| `get_l4_standard_profiles_state_tool()` | Read **current device settings** for the 5 standard profiles (e.g. idleTimeout, pvaAcceleration). Use this as **Before** when comparing. |
| `apply_l4_standard_db_tool()` | Apply L4 standard sys db + ltm connection (GUI, fastl4, syn cookie, monitorencap, mgmtroutecheck, setup.run). |
| `apply_l4_standard_profiles_tool()` | Create or update standard profiles: HTTP_DEFAULT, TCP_DEFAULT, FL4_DEFAULT, FL4_UDP, clientssl_sni_default. |

### Recommended flow (with verification)

To get a correct **before/after** report (and avoid showing wrong "before" values like default 120 instead of actual device 300):

1. **Before** — Call `get_l4_standard_db_state_tool()` and/or `get_l4_standard_profiles_state_tool()` and save the result.
2. **Apply** — Call `apply_l4_standard_db_tool()` and/or `apply_l4_standard_profiles_tool()`.
3. **After** — Call the same get tool(s) again and compare with the saved Before.

Detailed basic settings (Section 0) and L4 DB/profile list (Section 1): **`F5_TMOS_STANDARD_CONFIG_GUIDE.md`**.

---

## Documentation (Guides)

| File | Description |
|------|-------------|
| **`README.md`** (this file) | Overview, configuration, quick reference. |
| **`F5_TMOS_STANDARD_CONFIG_GUIDE.md`** | F5 TMOS standard process flow: basic settings (Section 0), L4 DB/Profile (Section 1), One-Arm, redundancy, VLAN/Self IP/Route, SNAT, profiles. Includes **verification flow** (Section 1.4). |
| **`TMOS_AI_AGENT_GUIDE.md`** | Full tool list (12 tools including apply_basic_settings_tool), usage examples, Claude Desktop setup, and AI agent behavior. |

New users: set `.env` (see Configuration above), then read `F5_TMOS_STANDARD_CONFIG_GUIDE.md` for the flow and `TMOS_AI_AGENT_GUIDE.md` for tool usage.

---

### Key Files

- **`F5MCPserver.py`**: The main server file that initializes the MCP server and defines the tools.
- **`Tools/F5object.py`**: A utility class for performing CRUD operations on F5 objects.

The repo also contains an example of the Claude desktop app config file.  
Only `F5object.py` is used from the Tools folder. The others were used in development.

**Commit after changes:** With **f5-mcp** open as your project folder, run **`./scripts/commit-if-changes.sh "무엇을 수정했는지 설명"`** (meaningful message required). See **`scripts/auto-commit-on-change.md`** for details.

### `It was tested with the Claude Desktop app. The MCP server was hosted in Windows WSL.`


<img width="362" alt="image" src="https://github.com/user-attachments/assets/06ac07e0-2ab7-4675-8c7b-c3809bc364ad" />

### Installing via Smithery

To install F5 Device Management Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@czirakim/F5.MCP.server):

```bash
npx -y @smithery/cli install @czirakim/F5.MCP.server --client claude
```


### Credits
This was written by Mihai Cziraki
