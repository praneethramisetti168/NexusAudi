#!/usr/bin/env python3
"""
NexusAudit Internal IPC Management CLI
Used by DevOps and local services to interact with nexus-manager daemon via /run/nexus/manager.sock
"""

import sys
import json
import socket
import argparse

SOCKET_PATH = "/run/nexus/manager.sock"

def send_ipc(payload):
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.sendall(json.dumps(payload).encode("utf-8"))
        
        response = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk
        client.close()
        return json.loads(response.decode("utf-8", errors="replace"))
    except FileNotFoundError:
        print(f"[-] Error: Socket {SOCKET_PATH} not found. Is nexus-manager service running?")
        sys.exit(1)
    except PermissionError:
        print(f"[-] Permission denied accessing {SOCKET_PATH}. Ensure your user is in the 'nexus' group.")
        sys.exit(1)
    except Exception as e:
        print(f"[-] IPC Communication error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="NexusAudit Core IPC Management Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Ping
    subparsers.add_parser("ping", help="Send ping health check to daemon")

    # Status
    subparsers.add_parser("status", help="Query daemon status and version")

    # Rotate logs
    subparsers.add_parser("rotate", help="Trigger audit log rotation")

    # Diag
    diag_parser = subparsers.add_parser("diag", help="Execute diagnostic module")
    diag_parser.add_argument("--module", default="/usr/lib/nexus/modules/sys_stat.so",
                             help="Path to diagnostic shared object (.so)")

    args = parser.parse_args()

    if args.command == "ping":
        res = send_ipc({"action": "ping"})
        print(f"[+] Response: {res}")
    elif args.command == "status":
        res = send_ipc({"action": "status"})
        print(f"[+] Status: {json.dumps(res, indent=2)}")
    elif args.command == "rotate":
        res = send_ipc({"action": "rotate_logs"})
        print(f"[+] Result: {res}")
    elif args.command == "diag":
        print(f"[*] Dispatching diagnostic module: {args.module}")
        res = send_ipc({"action": "load_diagnostic", "module": args.module})
        print(f"[+] Diagnostic Result: {json.dumps(res, indent=2)}")

if __name__ == "__main__":
    main()
