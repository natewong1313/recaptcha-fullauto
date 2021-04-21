from image_slicer import slice as image_slice
from dotenv import load_dotenv
import threading
import requests
import boto3
import glob
import os

load_dotenv()

image_types_conversions = {
    "crosswalks": "Zebra Crossing",
    "a fire hydrant": "Fire Hydrant",
    "cars": "Vehicle",
    "bicycles": "Bicycle",
    "bus": "Bus",
    "chimneys": "Roof",
    "traffic lights": "Traffic Light",
    "parking meters": "Parking Meter",
    "boats": "Boat",
    "motorcycles": "Motorcycle",
    "mountains or hills": "Landscape",
    "tractors": "Tractor",
    "taxis": "Taxi"
}

class ImageHandler:
    def __init__(self):
        if not os.path.exists("images"):
            os.makedirs("images")

        self.aws_rekognition_client = boto3.client("rekognition", aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID"), 
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"), region_name = os.getenv("AWS_REGION"))
        files = glob.glob(os.path.join(os.getcwd(), "images\\*"))
        for f in files:
            os.remove(f)
    
    def process_grid(self, image_grid_url, desired_image_type):
        self.save_image(image_grid_url, "images/captcha_grid.jpg", is_grid = True)
        
        image_worker_threads = []
        self.results = []
        for x in range(3):
            for y in range(3):
                index = (x*3) + y
                t = threading.Thread(target = self.process_image, args = (f"images/captcha_grid_0{x+1}_0{y+1}.png", desired_image_type, index))
                t.start()
                image_worker_threads.append(t)

        for t in image_worker_threads:
            t.join()

        return self.results
    
    def process_new_images(self, images_urls, desired_image_type):
        image_worker_threads = []
        self.results = []
        for i, image_url in enumerate(images_urls):
            self.save_image(image_url, f"images/captcha_img{i}.jpg")
            t = threading.Thread(target = self.process_image, args = (f"images/captcha_img{i}.jpg", desired_image_type, i))
            t.start()
            image_worker_threads.append(t)
        
        for t in image_worker_threads:
            t.join()
        
        new_images_results = []
        for i, image_url in enumerate(images_urls):
            new_images_results.append({"image_url": image_url, "matches": i in self.results})

        return new_images_results

    
    def save_image(self, image_url, path_name, is_grid = False):
        r = requests.get(image_url, stream = True)
        if r.status_code == 200:
            with open(path_name, "wb") as f:
                for chunk in r:
                    f.write(chunk)
            if is_grid:
                image_slice(path_name, 9)
        else:
            raise Exception(f"Unknown status code from image url: {r.status_code}")

    def process_image(self, image_path, desired_image_type, index):
        with open(os.path.join(os.getcwd(), image_path), "rb") as image:
            response = self.aws_rekognition_client.detect_labels(Image = {"Bytes": image.read()})
        for label in response["Labels"]:
            if image_types_conversions[desired_image_type] == label["Name"]:
                self.results.append(index)