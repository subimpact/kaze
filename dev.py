#!/usr/bin/env python3
"""
🍃 Kaze (風) — Local Development Server
Zero dependencies. Automatically rebuilds on content/template changes
and serves dist/ over HTTP.
"""

import os
import sys
import time
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import build

PORT = 8000
WATCH_DIRS = ['content', 'templates', 'static', 'admin']

def get_mtimes():
    mtimes = {}
    for d in WATCH_DIRS:
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                p = os.path.join(root, f)
                try:
                    mtimes[p] = os.path.getmtime(p)
                except OSError:
                    pass
    return mtimes

def watch_loop():
    last_mtimes = get_mtimes()
    while True:
        time.sleep(1)
        current_mtimes = get_mtimes()
        if current_mtimes != last_mtimes:
            print("\n🔄 Change detected, rebuilding...")
            try:
                build.build()
            except Exception as e:
                print(f"❌ Build error: {e}")
            last_mtimes = current_mtimes

def run_server():
    os.chdir(build.DIST_DIR)
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(('0.0.0.0', PORT), handler)
    print(f"\n🌐 Dev server running at http://localhost:{PORT}")
    print("   Press Ctrl+C to stop.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
        sys.exit(0)

if __name__ == '__main__':
    # Initial build
    build.build()

    # Start watcher thread
    watcher = threading.Thread(target=watch_loop, daemon=True)
    watcher.start()

    # Start HTTP server
    run_server()
