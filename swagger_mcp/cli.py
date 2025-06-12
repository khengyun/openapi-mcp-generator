import argparse

from .runtime import create_mcp_server


def _parse_key_values(items):
    result = {}
    for item in items:
        if "=" in item:
            k, v = item.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run an MCP server directly from an OpenAPI specification"
    )
    parser.add_argument("openapi_spec", help="Path or URL to the OpenAPI spec")
    parser.add_argument("--api-url", default="", help="Base URL for the API")
    parser.add_argument(
        "--auth-type",
        choices=["bearer", "token", "basic"],
        default="bearer",
        help="Authentication type",
    )
    parser.add_argument("--api-token", default="", help="API token for auth")
    parser.add_argument("--api-username", default="", help="Username for basic auth")
    parser.add_argument("--api-password", default="", help="Password for basic auth")
    parser.add_argument("--include-pattern", default="", help="Regex of operations to include")
    parser.add_argument("--exclude-pattern", default="", help="Regex of operations to exclude")
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="Extra header KEY=VALUE (repeatable)",
    )
    parser.add_argument(
        "--const",
        action="append",
        default=[],
        help="Constant query parameter KEY=VALUE (repeatable)",
    )
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="sse",
        help="Transport type",
    )

    args = parser.parse_args()
    headers = _parse_key_values(args.header)
    consts = _parse_key_values(args.const)

    mcp = create_mcp_server(
        args.openapi_spec,
        api_url=args.api_url,
        auth_type=args.auth_type,
        api_token=args.api_token,
        api_username=args.api_username,
        api_password=args.api_password,
        headers=headers,
        const_params=consts,
        include_pattern=args.include_pattern or None,
        exclude_pattern=args.exclude_pattern or None,
    )

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
