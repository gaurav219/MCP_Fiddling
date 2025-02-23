import asyncio
import json
import requests
import os
from typing import Optional
from contextlib import AsyncExitStack
import pdb
import ast

from mcp import ClientSession
from mcp.client.sse import sse_client

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

OPENROUTER_API_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
        # Store the context managers so they stay alive
        self._streams_context = sse_client(url=server_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session: ClientSession = await self._session_context.__aenter__()

        # Initialize
        await self.session.initialize()

        # List available tools to verify connection
        print("Initialized SSE client...")
        print("Listing tools...")
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def cleanup(self):
        """Properly clean up the session and streams"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{ 
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            },
        } for tool in response.tools]

        # print(available_tools)

        # Call OpenRouter API
        api_response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "openai/gpt-4o-mini",  # Modify the model if needed
                "messages": messages,
                "tools": available_tools
            }),

        )

        if api_response.status_code != 200:
            return f"Error: {api_response.status_code} - {api_response.text}"

        response_data = api_response.json()
        # print(response_data)
        # print("response_data")
        # return response_data["choices"][0]["message"]["content"]


        # Initial Claude API call
        # print("response1")
        # response = self.anthropic.messages.create(
        #     model="claude-3-5-sonnet-20241022",
        #     max_tokens=100,
        #     messages=messages,
        #     tools=available_tools
        # )

        # print("response2", api_response)

        # Process response and handle tool calls
        tool_results = []
        final_text = []

        # pdb.set_trace()

        tools = api_response.json()["choices"][0]["message"]["tool_calls"]


        for content in tools:
            # if content.type == 'text':
            #     final_text.append(content.text)
            # elif content.type == 'tool_use':
            tool_name = content["function"]["name"]
            tool_args = ast.literal_eval(content["function"]["arguments"])
            
            # Execute tool call
            result = await self.session.call_tool(tool_name, tool_args)
            # tool_results.append({"call": tool_name, "result": result})
            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

            # Continue conversation with tool results
            # if hasattr(content, 'text') and content.text:
            messages.append({
                "role": "assistant",
                "tool_calls": tools
            }),
            messages.append({
                "role": "tool",
                "name": tool_name,
                "tool_call_id": content["id"],
                "content": result.content[0].text
            })

            api_response = requests.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": "openai/gpt-4o-mini",  # Modify the model if needed
                    "messages": messages,
                }),
            )

            if api_response.status_code != 200:
                return f"Error: {api_response.status_code} - {api_response.text}"

                # # Get next response from Claude
                # response = self.anthropic.messages.create(
                #     model="claude-3-5-sonnet-20241022",
                #     max_tokens=1000,
                #     messages=messages,
                # )

                # final_text.append(response.content[0].text)


            response_data = api_response.json()
            final_text.append(response_data["choices"][0]["message"]["content"])
        
        return "\n".join(final_text)
    

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run client.py <URL of SSE MCP server (i.e. http://localhost:8080/sse)>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_sse_server(server_url=sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys
    asyncio.run(main())