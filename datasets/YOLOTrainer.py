from ultralytics import YOLO
model = YOLO('yolo11n.pt')
model.train(data='coco8.yaml', epochs=60, workers=0, batch=64, device=0)