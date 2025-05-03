from ultralytics import YOLO

for i in ['yolov8n.pt',"yolov9t.pt","yolov10n.pt", "yolo11n.pt","yolo12n.pt"]:    
    for j in range(50,200,25):
        print("-"*200)
        print(f"Training model f'yolo{i}n with {0} epochs.")
        model = YOLO(i)
        model.train(data='coco8.yaml', epochs=j, project=f'runs/train{i}-{j}')