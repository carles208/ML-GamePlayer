import socket
import json
from consoleController import Console


SEPARADOR = "<END>"

def recibir_mensajes(conn):
    global console
    console._loadState("1")
    console._pause_game()
    buffer = ""
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            console._unpause_game()
            buffer += data
            while SEPARADOR in buffer:
                mensaje, buffer = buffer.split(SEPARADOR, 1)
                json_data = json.loads(mensaje)
                print(f"\n[JSON recibido] {json_data}")
            console._send_input('action')
        except Exception as e:
            print(f"[Error recibiendo]: {e}")
            break

def start_server(host="127.0.0.1", port=65432):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((host, port))
    servidor.listen(1)
    print(f"[Esperando conexión en] {host}:{port}")
    conn, addr = servidor.accept()
    print(f"[Conectado con] {addr}")
    recibir_mensajes(conn)

console = Console('C:/Users/franc/Desktop/Emulator', 'Galaga')
start_server()