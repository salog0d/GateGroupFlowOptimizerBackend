import asyncio
from typing import Any, Dict, List, Optional
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools


class MCPClient:
    """
    Cliente para conectarse a tu MCP Server y ejecutar tools.
    Se cachea la sesión y los tools para evitar reconexiones innecesarias.
    """
    def __init__(self, host: Optional[str] = None):
        self.host = host or "http://127.0.0.1:8000/mcp"
        self._tools_cache: Dict[str, Any] = {}

    async def _ensure_tools(self):
        if self._tools_cache:
            return
        async with streamablehttp_client(self.host) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                self._tools_cache = {t.name: (t, session) for t in tools}

    async def list_tools(self) -> List[str]:
        await self._ensure_tools()
        return list(self._tools_cache.keys())

    async def call_tool(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        await self._ensure_tools()
        if name not in self._tools_cache:
            raise ValueError(f"Tool '{name}' no encontrada en MCP Server")
        tool, session = self._tools_cache[name]
        result = await tool.ainvoke(payload)
        return result if isinstance(result, dict) else {"result": result}