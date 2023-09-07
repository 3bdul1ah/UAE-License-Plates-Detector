import os
from ultralytics import YOLO
import cv2
import requests
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd

class ExcelDatabase:
    def __init__(self, filename='plates_data.xlsx'):
        self.filename = filename

    def save(self, plate_data):
        if not os.path.exists(self.filename):
            df = pd.DataFrame(columns=["Plate Category", "Plate Number", "State", "Image URL"])
            df.to_excel(self.filename, index=False, engine='openpyxl')

        df = pd.read_excel(self.filename, engine='openpyxl')

        new_data = pd.DataFrame([{
            "Plate Category": plate_data[0],
            "Plate Number": plate_data[1],
            "State": plate_data[2],
            "Image URL":image_url
        }])

        df = pd.concat([df, new_data], ignore_index=True)
        df.to_excel(self.filename, index=False, engine='openpyxl')

class LicensePlateDetector:
    def __init__(self, model_path, db):
        self.model = YOLO(model_path)
        self.threshold = 0.5
        self.db = db  # Database instance (Excel or any other in the future)

        self.specific_classes = [
            '0', '1', '2', '3', '4', '5', '6', '7', '8',
            '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
            'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q',
            'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
        ]

        self.state_classes = {
            'exp': 'Export',
            'new_DUBAI': 'Dubai',
            'new_RAK': 'Ras Al-Kaimah',
            'new_abudabi': 'Abu Dhabi',
            'new_ajman': 'Ajman',
            'new_am': 'Umm Al Quwain',
            'new_fujairah': 'Fujairah',
            'old_DUBAI': 'Dubai',
            'old_RAK': 'Ras Al-Kaimah',
            'old_abudabi': 'Abu Dhabi',
            'old_ajman': 'Ajman',
            'old_am': 'Umm Al-Quwain',
            'old_fujira': 'Fujairah',
            'old_sharka': 'Sharjah'
        }
    def detect_text(self, image, plate_category=None):
        plate_category
        plate_number = []
        state_name = "couldn't be detected"
        plate_string = ""
        category = []

        H, W, _ = image.shape
        results = self.model(image)[0]

        # Sort the results by the x-axis position
        sorted_results = sorted(results.boxes.data.tolist(), key=lambda x: x[0])

        for x1, y1, x2, y2, score, class_id in sorted_results:
            class_name = self.model.names[class_id]
            if score > self.threshold and class_name in self.state_classes:
                state_name = self.state_classes[class_name]
                break

        if state_name == 'Sharjah' or state_name == 'Abu Dhabi':
            for x1, y1, x2, y2, score, class_id in sorted_results:
                class_name = self.model.names[class_id]
                if score > self.threshold and class_name in self.specific_classes:
                    if y2 <= H // 2 or x2 <= W // 5:
                        category.append(class_name)
                    else:
                        plate_number.append(class_name)

            plate_string = ''.join(plate_number)
            plate_category = ''.join(category)

        else:
            for x1, y1, x2, y2, score, class_id in sorted_results:
                class_name = self.model.names[class_id]
                if score > self.threshold and class_name in self.specific_classes:
                    if class_name.isalpha():
                        category.append(class_name)
                    elif class_name.isdigit():
                        plate_number.append(class_name)

            plate_string = ''.join(plate_number)
            plate_category = ''.join(category)

        return plate_category, plate_string, state_name

    def process_image(self, image_url):
        response = requests.get(image_url)
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            image = cv2.imdecode(np.frombuffer(image_data.read(), np.uint8), cv2.IMREAD_COLOR)

            H, W, _ = image.shape

            results = self.model(image)[0]

            sorted_results = sorted(results.boxes.data.tolist(), key=lambda x: x[0])

            for result in sorted_results:
                x1, y1, x2, y2, score, class_id = result

                if score > self.threshold and results.names[int(class_id)] == 'plate':
                    cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
                    plate_img = image[int(y1):int(y2), int(x1):int(x2)]
                    plate_category, plate_number, state = self.detect_text(plate_img)
                    print(f"Plate category: {plate_category}")
                    print(f"Plate Number: {plate_number}")
                    print(f"Plate state: {state}")

                    self.db.save((plate_category, plate_number, state))

            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            print(f"Failed to retrieve image from URL: {image_url}")
            return None

    def display_image(self, processed_image):
        plt.figure()
        plt.imshow(processed_image)
        plt.show()


if __name__ == "__main__":
    model_path = os.path.join('.', 'runs', 'detect', 'train25', 'weights', 'best.pt')
    db = ExcelDatabase()
    detector = LicensePlateDetector(model_path, db)

    while True:  # loop to get multiple image URLs
        image_url = input('URL (Enter "exit" to stop):  ')
        if image_url.lower() == "exit":
            break
        processed_image = detector.process_image(image_url)
        if processed_image is not None:
            detector.display_image(processed_image)