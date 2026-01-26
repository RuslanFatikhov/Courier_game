#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Socket.IO smoke check. Requires AUTH_TOKEN in env.
"""

import os
import sys
import socketio


def main():
    token = os.environ.get("AUTH_TOKEN")
    if not token:
        print("AUTH_TOKEN is required in env")
        return 1

    url = os.environ.get("SOCKET_URL", "http://127.0.0.1:5200")

    sio = socketio.Client()

    @sio.event
    def connect():
        transport = getattr(sio, "transport", None)
        print(f"✅ Socket connected (transport={transport})")
        sio.emit("user_login", {})

    @sio.on("login_success")
    def on_login_success(data):
        print(f"✅ login_success: {data}")
        sio.disconnect()

    @sio.event
    def connect_error(data):
        print(f"❌ Socket connect error: {data}")

    try:
        sio.connect(url, transports=["polling"], auth=None, query_string=f"token={token}")
    except Exception as exc:
        print(f"❌ Socket error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
