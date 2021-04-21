# Recaptcha Fullauto
I've decided to open source my old Recaptcha v2 solver. My latest version will be opened sourced this summer. I am hoping this project will serve as inspiration for others to build a solver from, as plugging in an existing model is not too difficult to do.<br><br>
This project uses the AWS [Rekognition](https://aws.amazon.com/rekognition/) API, which is a decent solution but isn't the best. If you are looking to build off this project, I would take a look at [this repo](https://github.com/haze/nocap) for inspiration on building and training your own model. I would also reccomend using [this repo](https://github.com/deathlyface/recaptcha-dataset) as a base for your dataset or scraping images from Google Images using [this project](https://pypi.org/project/icrawler/).<br> 


https://user-images.githubusercontent.com/39974384/115634145-ff9b4900-a2d6-11eb-972c-838389a5c5f6.mp4


## Requirements
* Python 3
* Firefox
* Geckodriver (make sure it is installed in your PATH)
* AWS credentials (create a new IAM user with the AmazonRekognitionFullAccess role) 
## Installation
### Download The Project
```bash
git clone https://github.com/natewong1313/recaptcha-fullauto.git
```
```bash
cd recaptcha-fullauto
```
### Configuration
Add your proxies in the proxies.txt file and add your AWS credentials in the .env file<br>
If you don't want to use proxies, modify the src/main.py file as such
```python
rcs = RecaptchaSolver("https://www.google.com/recaptcha/api2/demo", use_proxies = False)
```
### Using Docker
```bash
docker build -t recaptcha-fullauto .
```
```bash
docker run recaptcha-fullauto
```
### From Source
```bash
pip install -r requirements.txt
```
```bash
python src/main.py
```
