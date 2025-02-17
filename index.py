from modelcontextprotocol_sdk.server import Server
from modelcontextprotocol_sdk.transport import StdioServerTransport
from modelcontextprotocol_sdk.types import ListResourcesRequestSchema, ReadResourceRequestSchema

print('Starting server...')

server = Server(
    name="example-server",
    version="1.0.0",
    capabilities={
        'resources': {}
    }
)

@server.request_handler(ListResourcesRequestSchema)
async def handle_list_resources_request():
    return {
        'resources': [
            {
                'uri': 'file:///example.txt',
                'name': 'Example Resource',
            },
        ],
    }

@server.request_handler(ReadResourceRequestSchema)
async def handle_read_resource_request(request):
    if request['params']['uri'] == 'file:///example.txt':
        return {
            'contents': [
                {
                    'uri': 'file:///example.txt',
                    'mimeType': 'text/plain',
                    'text': 'This is the content of the example resource.',
                },
            ],
        }
    else:
        raise Exception("Resource not found")

transport = StdioServerTransport()
await server.connect(transport)
print('Server connected and ready!')