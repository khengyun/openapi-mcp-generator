import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from swagger_mcp.runtime import create_mcp_server


async def _list_tool_names(mcp):
    tools = await mcp.list_tools()
    return [t.name for t in tools]


def test_runtime_parses_tools():
    mcp = create_mcp_server("tests/openapi.yaml", api_url="http://localhost")
    tool_names = asyncio.run(_list_tool_names(mcp))
    assert "getItems" in tool_names
    assert "createLegacyItem" in tool_names


def test_include_exclude_patterns():
    mcp_inc = create_mcp_server(
        "tests/openapi.yaml",
        api_url="http://localhost",
        include_pattern="legacy",
    )
    names_inc = asyncio.run(_list_tool_names(mcp_inc))
    assert names_inc == ["createLegacyItem"]

    mcp_exc = create_mcp_server(
        "tests/openapi.yaml",
        api_url="http://localhost",
        exclude_pattern="legacy",
    )
    names_exc = asyncio.run(_list_tool_names(mcp_exc))
    assert "createLegacyItem" not in names_exc
    assert "getItems" in names_exc
