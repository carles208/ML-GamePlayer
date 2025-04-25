from ultralytics import YOLO
model = YOLO('yolo11n.yaml')
model.train(data='coco8.yaml', epochs=1)
