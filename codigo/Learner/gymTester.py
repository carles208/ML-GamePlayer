import socket
import threading
import json
import pygetwindow as gw
import pyautogui
import time
from pynput.keyboard import Key, Controller


SEPARADOR = "<END>"

def _focus_game_window():
        windows = gw.getWindowsWithTitle("Galaga")
        if windows:
            game_window = windows[0]
            game_window.activate()
            time.sleep(0.001)
            return True
        else:
            return False


def recibir_mensajes(conn):
    buffer = ""
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            buffer += data
            while SEPARADOR in buffer:
                mensaje, buffer = buffer.split(SEPARADOR, 1)
                json_data = json.loads(mensaje)
                print(f"\n[JSON recibido] {json_data}")
        except Exception as e:
            print(f"[Error recibiendo]: {e}")
            break

def enviar_mensajes(conn):
    while True:
        try:
            x = '{ "name":"John", "age":30, "city":"New York"}'
            y = json.loads(x)
            mensaje = json.dumps(y) + SEPARADOR
            conn.sendall(mensaje.encode())
        except Exception as e:
            print(f"[Error enviando]: {e}")

def start_server(host="127.0.0.1", port=65432):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((host, port))
    servidor.listen(1)
    print(f"[Esperando conexión en] {host}:{port}")
    conn, addr = servidor.accept()
    print(f"[Conectado con] {addr}")

    threading.Thread(target=recibir_mensajes, args=(conn,), daemon=True).start()
    enviar_mensajes(conn)

start_server()