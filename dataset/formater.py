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
os.makedirs(os.path.join(OUTPUT_DIR, "annotations"),      exist_ok=True)

# Listado de sprites y mapeo de categorías
sprite_files = [f for f in os.listdir(SPRITES_DIR) if f.endswith(".png")]
categories   = []
category_map = {}
for i, name in enumerate(sprite_files):
    label = os.path.splitext(name)[0]
    categories.append({"id": i+1, "name": label, "supercategory": ""})
    category_map[name] = i+1

# Inicializamos COCO para train y val
coco_train = {"images": [], "annotations": [], "categories": categories}
coco_val   = {"images": [], "annotations": [], "categories": categories}

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
    new_w = int((h*sin) + (w*cos))
    new_h = int((h*cos) + (w*sin))
    M[0,2] += (new_w/2) - center[0]; M[1,2] += (new_h/2) - center[1]
    return cv2.warpAffine(sprite, M, (new_w, new_h),
                          flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT,
                          borderValue=(0,0,0,0))

annotation_id = 1

for img_id in range(1, NUM_IMAGES + 1):
    # Lienzo negro
    composite = np.zeros((IMG_HEIGHT, IMG_WIDTH, 3), dtype=np.float32)
    used_boxes = []
    num_sprites = random.randint(1, MAX_SPRITES_PER_IMAGE)
    tries = 0

    while len(used_boxes) < num_sprites and tries < 100:
        tries += 1
        sprite_name = random.choice(sprite_files)
        sprite = cv2.imread(os.path.join(SPRITES_DIR, sprite_name), cv2.IMREAD_UNCHANGED)
        if sprite is None:
            continue

        if random.random() < ROTATE_PROBABILITY:
            sprite = rotate_sprite(sprite)

        # dimensionamiento
        ratio = SPRITE_SIZE_RATIO * random.uniform(
            1 - SPRITE_SIZE_VARIATION,
            1 + SPRITE_SIZE_VARIATION
        )
        target_w = int(IMG_WIDTH * ratio)
        aspect   = sprite.shape[0] / sprite.shape[1]
        new_w, new_h = target_w, int(target_w * aspect)
        if new_w >= IMG_WIDTH or new_h >= IMG_HEIGHT:
            continue
        sprite = cv2.resize(sprite, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # posición aleatoria sin overlap
        max_x, max_y = IMG_WIDTH - new_w, IMG_HEIGHT - new_h
        x, y = random.randint(0, max_x), random.randint(0, max_y)
        if check_overlap(x, y, new_w, new_h, used_boxes):
            continue

        # composición alpha
        rgb   = sprite[:, :, :3].astype(np.float32) / 255.0
        alpha = sprite[:, :, 3].astype(np.float32) / 255.0
        alpha = alpha[..., None]
        roi   = composite[y:y+new_h, x:x+new_w]
        composite[y:y+new_h, x:x+new_w] = alpha * rgb + (1 - alpha) * roi

        # agregar anotación
        ann = {
            "id": annotation_id,
            "image_id": img_id,
            "category_id": category_map[sprite_name],
            "bbox": [x, y, new_w, new_h],
            "area": new_w * new_h,
            "iscrowd": 0
        }
        if img_id <= IMAGES_PER_SPLIT:
            coco_train["annotations"].append(ann)
        else:
            coco_val["annotations"].append(ann)

        annotation_id += 1
        used_boxes.append((x, y, new_w, new_h))

    # guardar imagen en disco
    composite = (composite * 255).astype(np.uint8)
    filename = f"img_{img_id:04}.jpg"
    split    = "train" if img_id <= IMAGES_PER_SPLIT else "val"
    out_path = os.path.join(OUTPUT_DIR, "images", split, filename)
    cv2.imwrite(out_path, composite)

    img_info = {
        "id": img_id,
        "file_name": f"images/{split}/{filename}",
        "width": IMG_WIDTH,
        "height": IMG_HEIGHT
    }
    if img_id <= IMAGES_PER_SPLIT:
        coco_train["images"].append(img_info)
    else:
        coco_val["images"].append(img_info)

# Volcar JSON de anotaciones
with open(os.path.join(OUTPUT_DIR, "annotations", "instances_train.json"), "w") as f:
    json.dump(coco_train, f, indent=2)
with open(os.path.join(OUTPUT_DIR, "annotations", "instances_val.json"), "w") as f:
    json.dump(coco_val, f, indent=2)

# Generar archivo YAML de COCO8 para Ultralytics
coco8_yaml = f"""\
# COCO8 dataset ({NUM_IMAGES} imágenes: {IMAGES_PER_SPLIT} train, {NUM_IMAGES-IMAGES_PER_SPLIT} val)
path: .
train: images/train
val:   images/val

nc: {len(categories)}
names: {[c['name'] for c in categories]}
"""
with open(os.path.join(OUTPUT_DIR, "coco8.yaml"), "w") as f:
    f.write(coco8_yaml)

print(f"✅ Dataset COCO8 generado en '{OUTPUT_DIR}' con {NUM_IMAGES} imágenes ({IMAGES_PER_SPLIT} train, {NUM_IMAGES-IMAGES_PER_SPLIT} val).")
