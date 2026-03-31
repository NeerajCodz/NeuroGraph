"""Test route registration."""
from src.main import app

# List all memory routes
print('Memory routes in main app:')
for route in app.routes:
    if hasattr(route, 'path') and 'memory' in route.path:
        methods = getattr(route, 'methods', '?')
        print(f'  {methods} {route.path}')

# Check openapi
from fastapi.openapi.utils import get_openapi
openapi = get_openapi(title="test", version="1.0", routes=app.routes)
print('\nOpenAPI paths with memory:')
for path in openapi.get('paths', {}).keys():
    if 'memory' in path:
        print(f'  {path}')
