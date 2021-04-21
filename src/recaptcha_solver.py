from selenium import webdriver
from selenium.common.exceptions import MoveTargetOutOfBoundsException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from base64 import b64encode
from loguru import logger
import random
import time
import os
from utils import sleep_random, load_proxy
from recaptcha_task import RecaptchaTask
from image_handler import ImageHandler, image_types_conversions

class RecaptchaSolver:
    def __init__(self, solve_url, use_proxies = True, headless = False):
        options = Options()
        options.headless = headless

        profile = webdriver.FirefoxProfile() 
        if use_proxies:
            proxy = load_proxy()
            profile.set_preference("network.proxy.type", 1)
            profile.set_preference("network.proxy.http", proxy["ip"])
            profile.set_preference("network.proxy.http_port", proxy["port"])
            if "username" in proxy:
                credentials = b64encode(f'{proxy["username"]}:{proxy["password"]}'.encode("ascii")).decode()
                profile.set_preference("extensions.closeproxyauth.authtoken", credentials)

        profile.set_preference("dom.webdriver.enabled", False)
        profile.set_preference("useAutomationExtension", False)
        profile.update_preferences() 
        
        try:
            self.driver = webdriver.Firefox(firefox_profile = profile, options = options)
        except WebDriverException:
            options.headless = True
            self.driver = webdriver.Firefox(firefox_profile = profile, options = options)
            
        self.image_handler = ImageHandler()
        self.solve_url = solve_url
        self.recaptcha_task = RecaptchaTask()
    
    def solve(self):
        self.load_captcha_url()
        self.switch_to_recap_iframe()
        self.trigger_captcha()
        self.switch_to_challenge_iframe()
        while True:
            self.check_challenge_type()
            self.find_image_grid()
            self.solve_image_grid()
            self.solve_new_images()
            success = self.verify_challenge()
            if success:
                recaptcha_token = self.get_recaptcha_token()
                self.driver.quit()
                return recaptcha_token
        
    def load_captcha_url(self):
        logger.debug(f"Load url: {self.solve_url}")
        self.driver.get(self.solve_url)
    
    def switch_to_recap_iframe(self):
        logger.debug("Searching for recaptcha iframe")
        recaptcha_iframe = WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[title="reCAPTCHA"]')))
        logger.debug("Found iframe, switching to it...")
        self.driver.switch_to.frame(recaptcha_iframe.get_attribute("name"))
    
    def trigger_captcha(self):
        logger.debug("Searching for recaptcha checkbox")
        recaptcha_checkbox = WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.CLASS_NAME, "recaptcha-checkbox")))
        logger.debug("Found recaptcha checkbox, delaying before click...")
        sleep_random(1.0, 3.0)

        ActionChains(self.driver).move_to_element(recaptcha_checkbox).perform()
        recaptcha_checkbox.click()
    
    def switch_to_challenge_iframe(self):
        logger.debug("Switching back to parent frame")
        self.driver.switch_to.parent_frame()
        logger.debug("Searching for challenge iframe")
        recaptcha_challenge_iframe = WebDriverWait(self.driver, 25).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'iframe[title="recaptcha challenge"]')))
        logger.debug("Found challenge iframe, switching to it...")
        self.driver.switch_to.frame(recaptcha_challenge_iframe.get_attribute("name"))
    
    def check_challenge_type(self):
        while True:
            class_name = "rc-imageselect-desc-no-canonical"
            try:
                captcha_type = self.driver.find_element_by_class_name("rc-imageselect-desc-no-canonical").get_attribute("textContent")
            except NoSuchElementException:
                captcha_type = self.driver.find_element_by_class_name("rc-imageselect-desc").get_attribute("textContent")
                class_name = "rc-imageselect-desc"

            if "Select all squares with" in captcha_type:
                logger.debug("Fetching new challenge...")
                self.reload_captcha()
                continue
            elif "Select all images with" in captcha_type:
                desired_image_type = self.driver.find_element_by_class_name(class_name).find_element_by_tag_name("strong").get_attribute("textContent")
                if desired_image_type in image_types_conversions:
                    logger.debug(f"Challenge type found: {desired_image_type}")
                    self.recaptcha_task.desired_image_type = desired_image_type
                    return
                else:
                    logger.error(f"Unknown challenge type found ({desired_image_type}), reloading...")
                    self.reload_captcha()
                    continue
            else:
                raise Exception("Unknown challenge type")

    def find_image_grid(self):
        logger.debug("Searching for image grid")
        image_grid_url = self.driver.find_element_by_class_name("rc-image-tile-wrapper").find_element_by_tag_name("img").get_attribute("src")
        logger.debug(f"Found image grid: {image_grid_url}")
        self.recaptcha_task.image_grid_url = image_grid_url
        
    def solve_image_grid(self):
        while True:
            logger.debug("Processing images in grid")
            results = self.image_handler.process_grid(self.recaptcha_task.image_grid_url, self.recaptcha_task.desired_image_type)
            if len(results) == 0:
                logger.error("Failed to identify images, reloading")
                self.reload_captcha()
                time.sleep(1)
                continue
            for index in results:
                self.click_image_grid_elem(index)
            return
    
    def click_image_grid_elem(self, index):
        image_element = self.driver.find_elements_by_class_name("rc-image-tile-target")[index]
        ActionChains(self.driver).move_to_element(image_element).perform()
        image_element.click()
    
    def solve_new_images(self):
        while True:
            logger.debug("Sleeping before checking new images")
            time.sleep(5)
            logger.debug("Processing new images")
            new_images = self.driver.find_elements_by_class_name("rc-image-tile-11")
            new_images_urls = [new_image.get_attribute("src") for new_image in new_images]

            results = self.image_handler.process_new_images(new_images_urls, self.recaptcha_task.desired_image_type)
            for i, result in enumerate(results):
                if result["matches"]: 
                    self.click_new_image_elem(i)

            if len([result for result in results if result["matches"]]) == 0 or len([result for result in results if not result["matches"]]) == len(results):
                logger.debug("All new images solved, proceeding")
                return
    
    def get_element_index(self, image_url, new_images_urls):
        for i, new_image_url in enumerate(new_images_urls):
            if new_image_url == image_url:
                return i

    def click_new_image_elem(self, index):
        image_element = self.driver.find_elements_by_class_name("rc-image-tile-11")[index].find_element_by_xpath("..")
        ActionChains(self.driver).move_to_element(image_element).perform()
        image_element.click()
    
    def verify_challenge(self):
        logger.debug("Verifying challenge solution")
        self.driver.find_element_by_id("recaptcha-verify-button").click()
        time.sleep(1)
        
        self.driver.switch_to.parent_frame()
        self.switch_to_recap_iframe()
        try:
            self.driver.find_element_by_class_name("recaptcha-checkbox-checked")
            logger.success("Successfully solved challenge")
            return True
        except NoSuchElementException:
            logger.error("Failed to solve challenge, retrying")
            self.switch_to_challenge_iframe()
            if self.driver.find_element_by_class_name("rc-imageselect-incorrect-response").get_attribute("style") != "":
                self.reload_captcha()
            return False
    
    def get_recaptcha_token(self):
        logger.debug("Searching for recaptcha token")
        self.driver.switch_to.parent_frame()
        recaptcha_token = self.driver.find_element_by_id("g-recaptcha-response").get_attribute("value")
        logger.debug(f"Found recaptcha token: {recaptcha_token}")
        return recaptcha_token

    def reload_captcha(self):
        old_val = self.driver.find_element_by_id("recaptcha-token").get_attribute("value")
        self.driver.find_element_by_id("recaptcha-reload-button").click()
        while True:
            if self.driver.find_element_by_id("recaptcha-token").get_attribute("value") != old_val:
                return
            time.sleep(0.01)