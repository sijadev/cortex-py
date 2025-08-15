#!/usr/bin/env python3
"""
Check what's available in mcp.server.models
"""

from mcp.server.models import *
import mcp.server.models as models

print("Available in mcp.server.models:", dir(models))

# Look for notification-related classes
for item in dir(models):
    if 'notification' in item.lower() or 'option' in item.lower():
        print(f"Found: {item}")

# Try different approaches
try:
    from mcp.server import NotificationOptions
    print("NotificationOptions found in mcp.server")
except ImportError:
    print("NotificationOptions not in mcp.server")

try:
    from mcp import NotificationOptions
    print("NotificationOptions found in mcp")
except ImportError:
    print("NotificationOptions not in mcp")

# Let's check what parameters get_capabilities actually needs
from mcp.server import Server
server = Server("test")

import inspect
sig = inspect.signature(server.get_capabilities)
print(f"get_capabilities signature: {sig}")
