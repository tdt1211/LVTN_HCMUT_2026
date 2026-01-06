# module/train.py
import cv2
import os
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HAAR_FACE = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")

def train_model(data_path="data", model_path="models/face_model.yml", max_images_per_person=10):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(HAAR_FACE)

    faces, labels = [], []
    label_map = {}
    current_id = 0

    for person in os.listdir(data_path):
        person_path = os.path.join(data_path, person)
        if not os.path.isdir(person_path):
            continue

        label_map[current_id] = person
        img_names = os.listdir(person_path)[:max_images_per_person]
        for img_name in img_names:
            img_path = os.path.join(person_path, img_name)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            faces.append(img)
            labels.append(current_id)
        current_id += 1

    recognizer.train(faces, np.array(labels))
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    recognizer.write(model_path)
    print(f"[INFO] Model trained and saved to {model_path}")

    # Save label mapping
    with open("models/label_map.txt", "w", encoding="utf-8") as f:
        for k, v in label_map.items():
            f.write(f"{k}:{v}\n")
