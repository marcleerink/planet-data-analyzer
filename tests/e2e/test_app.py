import time
from seleniumbase import BaseCase
import cv2
import pytest
import warnings

#TODO change streamlit version to fix this. Currently need this specific version of streamlit for the app to work properly
warnings.filterwarnings("ignore", category=DeprecationWarning) 

APP_URL = "http://localhost:8501"
# TODO: split to integration test exact match, multiple browsers


class ComponentsTest(BaseCase):
    current_screenshot_path = "tests/resources/screenshots/current-screenshot.png"
    reference_screenshot_path = "tests/resources/screenshots/reference-screenshot.png"

    @pytest.mark.last
    def test_app_screenshot_e(self):

        # Open the app and take a screenshot
        self.open(APP_URL)
        time.sleep(10)
        self.save_screenshot(self.current_screenshot_path)

        # Test that page has identical structure to baseline
        self.check_window(name="current_test", level=2)

        # Check folium app-sepecific parts
        # Main
        self.assert_text("Planets Satellite Imagery")

        # Filters
        self.assert_text("Satellite Providers")
        self.assert_text("Start Date")
        self.assert_text("End Date")
        self.assert_text("Cloud Cover Threshold")
        self.assert_text("Country")

        # # TODO include exact math
        # # Test screenshots look exactly the same
        # original = cv2.imread(self.current_screenshot_path)
        # reference = cv2.imread(self.reference_screenshot_path)

        # assert original.shape == reference.shape

        # difference = cv2.subtract(original, reference)
        # b, g, r = cv2.split(difference)
        # assert cv2.countNonZero(b) == cv2.countNonZero(g) == cv2.countNonZero(r) == 0
