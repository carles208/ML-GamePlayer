import os
import cv2
import json
import random
import numpy as np

# Configuración inicial
SPRITES_DIR           = "sprites/"          # Carpeta con sprites PNG
BACKGROUND_PATH       = "background.png"    # Imagen de fondo (no usada si creas lienzo en negro)
OUTPUT_DIR            = "coco8/"            # Salida en formato COCO8
NUM_IMAGES            = 200                 # 200 imágenes en total
TRAIN_RATIO           = 0.8                  # 80% para train
IMAGES_PER_SPLIT      = int(NUM_IMAGES * TRAIN_RATIO)  # 160 train, 40 val
MAX_SPRITES_PER_IMAGE = 30
IMG_WIDTH, IMG_HEIGHT = 2160, 2880
ROTATE_PROBABILITY    = 0.3
SPRITE_SIZE_RATIO     = 0.1
SPRITE_SIZE_VARIATION = 0.05

# Crear estructura de carpetas
os.makedirs(os.path.join(OUTPUT_DIR, "images", "train"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "images", "val"),   exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "labels", "train"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "labels", "val"),   exist_ok=True)

# Listado de sprites y mapeo de categorías
sprite_files = [f for f in os.listdir(SPRITES_DIR) if f.endswith(".png")]
categories   = []
category_map = {}
for i, name in enumerate(sprite_files):
    label = os.path.splitext(name)[0]
    categories.append(label)
    category_map[name] = i  # yolo txt usa índices 0-based

def check_overlap(x, y, w, h, boxes):
    for bx, by, bw, bh in boxes:
        if not (x + w <= bx or x >= bx + bw or y + h <= by or y >= by + bh):
            return True
    return False

def rotate_sprite(sprite):
    angle = random.uniform(0, 360)
    (h, w) = sprite.shape[:2]
    center = (w//2, h//2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(M[0,0]); sin = abs(M[0,1])
    new_w = int(h*sin + w*cos)
    new_h = int(h*cos + w*sin)
    M[0,2] += new_w/2 - center[0]
    M[1,2] += new_h/2 - center[1]
    return cv2.warpAffine(sprite, M, (new_w, new_h),
                          flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT,
                          borderValue=(0,0,0,0))

for img_id in range(1, NUM_IMAGES + 1):
    composite = np.zeros((IMG_HEIGHT, IMG_WIDTH, 3), dtype=np.float32)
    used_boxes = []
    num_sprites = random.randint(1, MAX_SPRITES_PER_IMAGE)
    tries = 0

    labels = []  # aquí almacenamos las líneas de etiqueta

    while len(used_boxes) < num_sprites and tries < 100:
        tries += 1
        sprite_name = random.choice(sprite_files)
        sprite = cv2.imread(os.path.join(SPRITES_DIR, sprite_name), cv2.IMREAD_UNCHANGED)
        if sprite is None:
            continue

        if random.random() < ROTATE_PROBABILITY:
            sprite = rotate_sprite(sprite)

        ratio = SPRITE_SIZE_RATIO * random.uniform(1 - SPRITE_SIZE_VARIATION,
                                                   1 + SPRITE_SIZE_VARIATION)
        target_w = int(IMG_WIDTH * ratio)
        aspect   = sprite.shape[0] / sprite.shape[1]
        new_w, new_h = target_w, int(target_w * aspect)
        if new_w >= IMG_WIDTH or new_h >= IMG_HEIGHT:
            continue
        sprite = cv2.resize(sprite, (new_w, new_h), interpolation=cv2.INTER_AREA)

        max_x, max_y = IMG_WIDTH - new_w, IMG_HEIGHT - new_h
        x, y = random.randint(0, max_x), random.randint(0, max_y)
        if check_overlap(x, y, new_w, new_h, used_boxes):
            continue

        rgb   = sprite[..., :3].astype(np.float32) / 255.0
        alpha = sprite[..., 3].astype(np.float32) / 255.0
        alpha = alpha[..., None]
        roi   = composite[y:y+new_h, x:x+new_w]
        composite[y:y+new_h, x:x+new_w] = alpha*rgb + (1-alpha)*roi

        # calcular etiqueta YOLO
        class_id = category_map[sprite_name]
        x_center = (x + new_w/2) / IMG_WIDTH
        y_center = (y + new_h/2) / IMG_HEIGHT
        w_norm    = new_w / IMG_WIDTH
        h_norm    = new_h / IMG_HEIGHT
        labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")

        used_boxes.append((x, y, new_w, new_h))

    # guardar imagen
    composite = (composite * 255).astype(np.uint8)
    filename = f"img_{img_id:04}.jpg"
    split    = "train" if img_id <= IMAGES_PER_SPLIT else "val"
    img_path = os.path.join(OUTPUT_DIR, "images", split, filename)
    cv2.imwrite(img_path, composite)

    # guardar etiquetas
    label_path = os.path.join(OUTPUT_DIR, "labels", split, filename.replace(".jpg", ".txt"))
    with open(label_path, "w") as f:
        f.write("\n".join(labels))

# Generar archivo YAML para entrenar en formato TXT
yaml_content = f"""\
train: images/train
val:   images/val

nc: {len(categories)}
names: {categories}
"""
with open(os.path.join(OUTPUT_DIR, "coco8.yaml"), "w") as f:
    f.write(yaml_content)

print(f"✅ Generadas {NUM_IMAGES} imágenes con etiquetas TXT en '{OUTPUT_DIR}'")