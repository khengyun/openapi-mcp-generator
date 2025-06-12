import json
import re
from typing import Any, Dict, Optional

import httpx
import yaml
from mcp.server.fastmcp import Context, FastMCP

from openapi_mcp_generator import generators, parser


def _load_spec(source: str) -> Dict[str, Any]:
    """Load an OpenAPI spec from a file, directory or URL."""
    if re.match(r"https?://", source):
        resp = httpx.get(source)
        resp.raise_for_status()
        text = resp.text
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError:
            return json.loads(text)
    return parser.parse_openapi_spec(source)


def _filter_spec(spec: Dict[str, Any], include: Optional[str], exclude: Optional[str]) -> None:
    inc_re = re.compile(include) if include else None
    exc_re = re.compile(exclude) if exclude else None
    for path in list(spec.get("paths", {})):
        path_item = spec["paths"][path]
        for method in list(path_item.keys()):
            op = path_item[method]
            op_id = op.get("operationId", "")
            match = f"{method}:{path}:{op_id}"
            if inc_re and not inc_re.search(match):
                del path_item[method]
                continue
            if exc_re and exc_re.search(match):
                del path_item[method]
        if not path_item:
            del spec["paths"][path]


def create_mcp_server(
    openapi_source: str,
    *,
    api_url: str = "",
    auth_type: str = "bearer",
    api_token: str = "",
    api_username: str = "",
    api_password: str = "",
    headers: Optional[Dict[str, str]] = None,
    const_params: Optional[Dict[str, str]] = None,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
) -> FastMCP:
    """Create a FastMCP server from an OpenAPI specification."""

    spec = _load_spec(openapi_source)
    _filter_spec(spec, include_pattern, exclude_pattern)

    mcp = FastMCP(name=spec.get("info", {}).get("title", "API"))
    headers = headers or {}
    const_params = const_params or {}

    async def get_http_client() -> httpx.AsyncClient:
        base_url = api_url
        if not base_url and spec.get("servers"):
            base_url = spec["servers"][0].get("url", "")
        hdrs = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            **headers,
        }
        auth = None
        if auth_type == "bearer" and api_token:
            hdrs["Authorization"] = f"Bearer {api_token}"
        elif auth_type == "token" and api_token:
            hdrs["X-API-Key"] = api_token
        elif auth_type == "basic" and api_username and api_password:
            auth = httpx.BasicAuth(username=api_username, password=api_password)
        return httpx.AsyncClient(base_url=base_url, headers=hdrs, auth=auth, timeout=30.0)

    exec_globals = {
        "mcp": mcp,
        "Context": Context,
        "httpx": httpx,
        "get_http_client": get_http_client,
        "const_query_params": const_params,
    }

    tool_defs = generators.generate_tool_definitions(spec)
    if const_params:
        tool_defs = tool_defs.replace(
            "query_params = {}", "query_params = const_query_params.copy()"
        )
    resource_defs = generators.generate_resource_definitions(spec)
    exec(tool_defs + "\n" + resource_defs, exec_globals)

    return mcp
