import os
from ultralytics import YOLO
import cv2
import requests
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt

model_path = os.path.join('.', 'runs', 'detect', 'train23', 'weights', 'last.pt')

specific_classes = ['0', '1', '2', '3', '4', '5', '6', '7', '8',
                    '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                    'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q',
                    'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
state_classes = {
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

# Load a model
model = YOLO(model_path)  # load a custom model

threshold = 0.4


def detect_text(image):
    output_array = []
    state_name = "couldn't be detected"
    plate_category = None
    plate_number = ""

    H, W, _ = image.shape
    results = model(image)[0]

    # Sort the results by the x-axis position
    sorted_results = sorted(results.boxes.data.tolist(), key=lambda x: x[0])

    for x1, y1, x2, y2, score, class_id in sorted_results:
        class_name = model.names[class_id]

        if (score > threshold) and (class_name in specific_classes):
            output_array.append(class_name)
        elif score > threshold and (class_name in state_classes):
            state_name = state_classes[class_name]
            break

    number_list = []

    for char in output_array:
        if char.isdigit():
            number_list.append(char)

    if len(number_list) == 1 and (state_name in ['Abu Dhabi', 'Sharjah']):
        plate_category = number_list[0]
    elif len(number_list) > 1:
        plate_number = ''.join(number_list)
        if len(output_array) > len(number_list):
            plate_category = output_array[0]

    return plate_category, plate_number, state_name


def main():
    # URL list containing image URLs
    image_urls = [input('Enter Url: ')]


    for image_url in image_urls:
        response = requests.get(image_url)
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            image = cv2.imdecode(np.frombuffer(image_data.read(), np.uint8), cv2.IMREAD_COLOR)

            H, W, _ = image.shape

            results = model(image)[0]

            sorted_results = sorted (results.boxes.data.tolist (), key=lambda x: x[0])

            for result in sorted_results:
                x1, y1, x2, y2, score, class_id = result

                if score > threshold and results.names[int(class_id)] == 'plate':
                    cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
                    plate_img = image[int(y1):int(y2), int(x1):int(x2)]
                    plate_category, plate_number, state = detect_text(plate_img)
                    print(f"Plate category: {plate_category}")
                    print(f"Plate Number: {plate_number}")
                    print(f"Plate Emireties: {state}")


            plt.figure()
            plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            plt.show()

        else:
            print(f"Failed to retrieve image from URL: {image_url}")


if __name__ == "__main__":
    main()
