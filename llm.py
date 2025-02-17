# import requests
# import json
# # from dotenv import load_dotenv, dotenv_values 

# code = """arr = [10, 102, 30, 42, 232]

# n = len(arr)
# for i in range(n - 1):
#     for j in range(n - i - 1):
#         if arr[j] > arr[j + 1]:
#             arr[j], arr[j + 1] = arr[j + 1], arr[j]

# print(arr)"""

# response = requests.post(
#   url="https://openrouter.ai/api/v1/chat/completions",
#   headers={
#     "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
#     "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
#   },
#   data=json.dumps({
#     # "models": ["anthropic/claude-3.5-sonnet", "gryphe/mythomax-l2-13b"],
#     "models": ["openai/gpt-4o-mini"],
#     # "models": ["openai/o1-preview"],
#     "messages": [
#       {
#         "role": "user",
#         # "content": "What's the output of the code?\n\n" + code
#         "content": "Sachin Tendulkar vs Virat Kohli?\n\n"
#       }
#     ]
#   })
# )
# # Extract and print the response content
# if response.status_code == 200:
#     result = response.json()
#     # print(result)
#     print(result["choices"][0]["message"]["content"])
# else:
#     print("Error:", response.status_code, response.text)
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
# from mcp import Server
from starlette.routing import Route

app = Server("OpenRouter")
sse = SseServerTransport("/messages")

async def handle_sse(scope, receive, send):
    async with sse.connect_sse(scope, receive, send) as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())

async def handle_messages(scope, receive, send):
    await sse.handle_post_message(scope, receive, send)

starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)

import asyncio
from mcp import ServerSession, StdioServerTransport, tool

class MCPServer:
    def __init__(self):
        self.session = None

    async def start(self):
        """Initialize and run the MCP server."""
        transport = StdioServerTransport()
        self.session = ServerSession(transport)
        self.session.add_tool(self.echo_tool)
        await self.session.run()

    @tool
    async def echo_tool(self, text: str) -> str:
        """A simple tool that echoes back the input text."""
        return f"Echo: {text}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')

# # Optionally expose other important items at package level
# __all__ = ['main', 'server']