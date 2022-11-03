from seleniumbase import BaseCase
import cv2
import time
import subprocess


DEV_URL = "http://localhost:8501"

class ComponentsTest(BaseCase):
    def test_app_basic(self):

        # open the app and take a screenshot
        self.open(DEV_URL)

        time.sleep(10)  # give leaflet time to load from web
        self.save_screenshot("tests/resources/screenshots/current-screenshot.png")
       
        self.check_window(name="first_test", level=2)
        self.assert_text("Satellite Image Joins")

        # test screenshots look exactly the same
        original = cv2.imread(
            "tests/resources/screenshots/first-screenshot.png"
        )
        duplicate = cv2.imread("tests/resources/screenshots/current-screenshot.png")

        assert original.shape == duplicate.shape

        difference = cv2.subtract(original, duplicate)
        b, g, r = cv2.split(difference)
        assert cv2.countNonZero(b) == cv2.countNonZero(g) == cv2.countNonZero(r) == 0