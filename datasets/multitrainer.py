from ultralytics import YOLO

# python multitrainer.py > comparacionModelos.txt
#'yolov8n.pt,"yolov9t.pt","yolov10n.pt", "yolo11n.pt","yolo12n.pt"
#  ("yolo12n.pt", 32), ("yolo12s.pt", 32), ("yolo12m.pt", 32), ("yolo12l.pt", 16), 
for i in [("yolo12x.pt", 16)]:    
    print("-"*200)
    print(f"Training model f'yolo{i[0]}n with 100 epochs.")
    model = YOLO(i[0])
    model.train(data='coco8.yaml', epochs=100, project=f'runs/trainT{i[0]}-{i[1]}', workers=0, batch=i[1], device=0)