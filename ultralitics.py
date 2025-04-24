from ultralytics import YOLO
model = YOLO('yolo11n.pt')
model.train(data='C:/Users/carli/Desktop/Master/ML-GamePlayer/dataset/coco8/coco8.yaml', epochs=3)
