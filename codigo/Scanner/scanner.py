import json
from ultralytics import YOLO
from capture import Capturer
import pytesseract
import cv2 as cv
import socket
import win32gui
import json
import numpy as np

SEPARADOR = "<END>"

MODEL_DIR = 'scanner/models/best11n75.pt'

conn = None

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

def enviar_mensajes(client, data):
    try:
        mensaje = json.dumps(data) + SEPARADOR
        client.sendall(mensaje.encode())
    except Exception as e:
        print(f"[Error enviando]: {e}")

def start_server(host="127.0.0.1", port=65432):
    global client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))

    # Debug
    #threading.Thread(target=recibir_mensajes, args=(conn,), daemon=True).start()
    #enviar_mensajes(conn)

def find_window_by_partial_title(partial_title: str):
    """
    Devuelve el primer HWND cuya ventana contenga `partial_title`
    en su título (búsqueda case-insensitive), o None si no hay coincidencias.
    """
    matches = []

    def _enum(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if partial_title.lower() in title.lower():
            matches.append((hwnd, title))
    win32gui.EnumWindows(_enum, None)

    if not matches:
        return None
    # Si hay varias coincidencias, podemos elegir la primera
    return matches[0][0]

def resize_window(partial_title: str, width: int, height: int):
    # 1. Encuentra el HWND por título parcial
    hwnd = find_window_by_partial_title(partial_title)
    if not hwnd:
        raise RuntimeError(f"No se encontró ninguna ventana con “{partial_title}” en el título")

    # 2. Lee su posición actual
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    x, y = left, top

    # 3. Mueve y redimensiona
    win32gui.MoveWindow(hwnd, x, y, width, height, True)

class Scanner:
    def __init__(self, windowName, delay, activateDelay, model, size):
        self.capturer = Capturer(windowName, delay, activateDelay)
        self.model = YOLO(model)
        self.model.to('cuda')
        self.prev_crop  = None     # recorte anterior
        self.prev_score = ''       # score extraído anteriormente
        self.i = 0
        self.plot = False
        self.results = []
        self.times = []
        self.framesStart = 50
        self.frameEnd = 300
        x, y = size
        resize_window(windowName, x, y)
    
    def startScanner(self):
        while True:
            capture = self.capturer.captureIMG()
            
            # Inferencia con YOLOv8
            analysis  = self.model.predict(capture, conf=0.40)
            res       = analysis[0]          # <-- aquí guardamos el Results, no la imagen
            annotated = res.plot()          # <-- annotated es ahora un ndarray RGB

            # Marcar centros normalizados usando res.boxes, no annotated.boxes
            h, w = capture.shape[:2]
            for xcn, ycn, _, _ in res.boxes.xywhn.cpu().numpy():
                cx, cy = int(xcn * w), int(ycn * h)
                cv.circle(annotated, (cx, cy), radius=4, color=(0,0,255), thickness=-1)

            # Recuadro de texto
            x1_frac, x2_frac = 0.05, 0.26
            y1_frac, y2_frac = 0.075, 0.097

            # 3. Convierte porcentajes a píxeles
            x1, x2 = int(x1_frac * w), int(x2_frac * w)
            y1, y2 = int(y1_frac * h), int(y2_frac * h)
 
            # 5. Dibuja el rectángulo escalable y refinado
            cv.rectangle(
                    annotated,
                    (x1, y1),
                    (x2, y2),
                    color=(0, 255, 0),
                    thickness=3
            )

            crop = capture[y1:y2, x1:x2]
            #cv.imwrite('score_crop.png', crop)

            if self.prev_crop is not None and np.array_equal(crop, self.prev_crop):
                score = self.prev_score
            else:
                # 2. Pasar a gris y ecualizar
                gray = cv.cvtColor(crop, cv.COLOR_BGR2GRAY)
                eq   = cv.equalizeHist(gray)

                # 3. Binarizar con Otsu
                _, bw  = cv.threshold(eq, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

                # 5. OCR con Tesseract (sólo dígitos)
                # 3) Configura Tesseract para que sólo detecte dígitos y trate todo como una línea
                pytesseract.pytesseract.tesseract_cmd = 'C:\Program Files\Tesseract-OCR/tesseract.exe'  # your path may be different
                custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'

                # 4) Llama a Tesseract
                score = pytesseract.image_to_string(bw, config=custom_config)

                # Guardamos para la próxima iteración
                self.prev_crop  = crop.copy()
                self.prev_score = ''.join(filter(str.isdigit, score))

            # 6. Filtrar y mostrar sólo los números
            print("Score detectado:", score)

            # Mostrar con OpenCV
            annotated = cv.cvtColor(annotated, cv.COLOR_RGB2BGR)
            cv.imshow('Detecciones YOLOv8', annotated)
            cv.waitKey(1)

            # Prepara la lista de detecciones
            detections = []
            for i, (xcn, ycn, _, _) in enumerate(res.boxes.xywhn.cpu().numpy(), start=1):
                cls_idx   = int(res.boxes.cls[i-1].item())
                class_name = self.model.names[cls_idx]
                detections.append({
                    "id":       f"det_{i:03}",       # det_001, det_002, ...
                    "class":    class_name,
                    "position": (float(xcn), float(ycn))
                })

            # Empaqueta todo en un dict y vuelca a JSON
            output = {"detections": detections, "score":score}
            json_str = json.dumps(output, indent=2)

            if self.plot:
                self.i += 1
                if self.i > self.framesStart:
                    for conf in enumerate(res.boxes.conf.cpu().numpy(), start=1):
                        self.results.append(conf[1])
                    self.times.append(res.speed['inference'])
                if self.i > self.frameEnd:
                    with open("Plot.txt", 'w') as f:
                        f.write('Conf. mean: ' + str(float(np.mean(self.results))) + '\n')
                        f.write('Time mean: ' + str(float(np.mean(self.times))) + '\n')
                    exit()
            
            enviar_mensajes(client, json_str)


start_server()
scan = Scanner("Galaga", 0.001, True, MODEL_DIR, (728,1024))
scan.startScanner()