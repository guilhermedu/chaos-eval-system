# probe/app_echo_server.py
import socket
import threading
import argparse


def handle_client(conn, addr):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            # aqui no futuro podes meter lógica de "chat" ou "file storage"
            conn.sendall(b"PONG\n")
    finally:
        conn.close()


def run_server(host="0.0.0.0", port=9000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)
    print(f"[APP-SERVER] Listening on {host}:{port}")
    while True:
        conn, addr = s.accept()
        print(f"[APP-SERVER] New connection from {addr}")
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()
    run_server(args.host, args.port)
