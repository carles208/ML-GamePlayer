import pygetwindow as gw
import pyautogui
from PIL import Image

# Nombre parcial o completo de la ventana que quieres capturar
window_name = "Steam"

# Obtener ventana por nombre
windows = gw.getWindowsWithTitle(window_name)

if not windows:
    print(f"No se encontró ninguna ventana con el nombre '{window_name}'")
else:
    window = windows[0]
    window.activate()
    pyautogui.sleep(1)  # Espera a que la ventana se active completamente

    # Capturar región específica de la ventana
    screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))

    # Guardar la captura
    screenshot.save("captura_ventana.png")
    print("Captura guardada como 'captura_ventana.png'")
