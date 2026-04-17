import json
import os
import socket
import threading

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))

MAX_PLAYERS = 4

clients = []
clients_lock = threading.Lock()


def send_message(conn, payload):
    data = (json.dumps(payload) + "\n").encode("utf-8")
    conn.sendall(data)


def broadcast(data, sender=None):
    with clients_lock:
        targets = list(clients)

    for conn in targets:
        if conn is sender:
            continue
        try:
            send_message(conn, data)
        except OSError:
            remove_client(conn)


def remove_client(conn):
    with clients_lock:
        if conn in clients:
            clients.remove(conn)
    try:
        conn.close()
    except OSError:
        pass


def handle_client(conn, player_id):
    try:
        send_message(conn, {"type": "welcome", "player_id": player_id})
        buffer = ""

        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break

            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                raw_message, buffer = buffer.split("\n", 1)
                if not raw_message.strip():
                    continue
                data = json.loads(raw_message)
                if isinstance(data, dict):
                    broadcast(data, sender=conn)
    except (ConnectionError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        print("player disconnected")
    finally:
        remove_client(conn)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

print("Server started on port", PORT)

player_id = 0

while True:
    conn, addr = server.accept()

    with clients_lock:
        if len(clients) >= MAX_PLAYERS:
            conn.close()
            continue
        clients.append(conn)

    print("Connected:", addr)

    thread = threading.Thread(
        target=handle_client,
        args=(conn, player_id),
        daemon=True,
    )

    thread.start()

    player_id += 1
