import math
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import mss
import numpy as np

from settings import CONFIG


class Blume:
    def __init__(self) -> None:
        self.clicked_points = []
        self.nearby_object_colors_hsv = np.array([
            self.bgr_to_hsv(rgb)
            for rgb in CONFIG.GREEN_OBJ_COLORS + CONFIG.BLUE_OBJ_COLORS
        ])
        self.nearby_bomb_object_hsv = np.array([
            self.bgr_to_hsv(rgb) for rgb in CONFIG.BOMB_COLLORS
        ])
        self.lower_green_hvs = np.array([30, 100, 120])
        self.upper_green_hvs = np.array([85, 255, 255])
        self.lower_blue_hsv = np.array([90, 50, 190])
        self.upper_blue_hsv = np.array([130, 255, 255])
        self.lower_red_hsv = np.array([170, 50, 50])
        self.upper_red_hsv = np.array([180, 255, 255])
        self.executor = ThreadPoolExecutor(max_workers=CONFIG.TPOOL_WORKERS)

    def bgr_to_hsv(self, hex_color):
        """Convert a hex color to hsv format."""
        hex_color = hex_color.lstrip("#")
        rgb = np.array(
            [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.uint8
        )
        hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)
        return hsv[0][0]

    def click_on_object(self, x_c, y_c):
        subprocess.run(f"xdotool mousemove {x_c} {y_c} click 1".split(" "))

    def detect_blume_app_position(self):
        """Detect the application window's position and size."""
        code = ["xwininfo", "-int"]
        result = subprocess.run(code, capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if len(line.split(":")) > 1:
                value = line.split(":")[1].strip()
            if "Window id" in line:
                self.window_id = line.split(":")[2].split()[0].strip()
            if "Absolute upper-left X:" in line:
                self.x_root = int(value)
            if "Absolute upper-left Y:" in line:
                self.y_root = int(value)
            if "Width" in line:
                self.width_position = int(value)
            if "Height" in line:
                self.height_position = int(value)

    def detect_green_or_blue_objects(self, frame):
        """Detect green or blue objects in the given frame."""
        hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask_green = cv2.inRange(hsv_img, self.lower_green_hvs, self.upper_green_hvs)

        if CONFIG.CLICK_BLUE_OBJECT:
            mask_blue = cv2.inRange(hsv_img, self.lower_blue_hsv, self.upper_blue_hsv)
            mask_combined = cv2.bitwise_or(mask_green, mask_blue)
            _, mask_thresh = cv2.threshold(mask_combined, 180, 255, cv2.THRESH_BINARY)
        else:
            _, mask_thresh = cv2.threshold(mask_green, 180, 255, cv2.THRESH_BINARY)

        # Remove noise(small dot)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_eroded = cv2.morphologyEx(mask_thresh, cv2.MORPH_OPEN, kernel)

        # Detect objects
        contours, _ = cv2.findContours(
            mask_eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        large_contours = [
            cnt for cnt in contours if cv2.contourArea(cnt) > CONFIG.MIN_OBJECT_AREA
        ]
        return large_contours

    def detect_white_rectangles(self, frame):
        """Detect white rectangles in the frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        objects, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for object in objects:
            epsilon = 0.02 * cv2.arcLength(object, True)
            approx = cv2.approxPolyDP(object, epsilon, True)
            area = cv2.contourArea(object)
            # 4 vertices
            if len(approx) == 4:
                # minimum play button area
                if area > CONFIG.MIN_PLAY_AREA:
                    x, y, w, h = cv2.boundingRect(object)
                    # Inside the bounding rectangle
                    roi = frame[y : y + h, x : x + w]
                    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                    mask = cv2.inRange(hsv_roi, self.lower_red_hsv, self.upper_red_hsv)
                    # Check if there are any red pixels in the region
                    if np.any(mask > 0):
                        return x + w // 2, y + h // 2

    def draw_and_debug_results(self, frame_np, contours=None):
        """Draw detected contours on the frame_np and display it."""
        if contours:
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(
                    frame_np, (x, y), (x + w, y + h), (0, 255, 0), 2
                )  # Draw green rectangles

        window_name = "Detected Objects"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(
            window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
        )

        cv2.imshow(window_name, frame_np)
        cv2.waitKey(CONFIG.DISPLAY_DELAY_MS)  # 3s delay to reduce CPU usage
        cv2.destroyAllWindows()

    def check_color_proximity(self, frame, bounding_box, radius=3):
        """Check if the bounding box contains nearby object colors."""
        hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        x, y, w, h = bounding_box

        start_x = max(x - radius, 0)
        start_y = max(y - radius, 0)
        end_x = min(x + w + radius, frame.shape[1])
        end_y = min(y + h + radius, frame.shape[0])

        region = hsv_img[start_y:end_y, start_x:end_x]
        gray_pixel_count = 0

        for gray_hsv in self.nearby_bomb_object_hsv:
            diff_gray = np.abs(region - gray_hsv)
            gray_matches = np.all(diff_gray <= [1, 50, 50], axis=-1)
            gray_pixel_count += np.sum(gray_matches)
            if (
                gray_pixel_count > 3
            ):  # Skip this object if more than 5 gray pixels are found
                if CONFIG.DEBUG:
                    gray_positions = np.argwhere(gray_matches)
                    for pos in gray_positions:
                        pixel_x = start_x + pos[1]
                        pixel_y = start_y + pos[0]
                        cv2.circle(
                            frame,
                            (pixel_x, pixel_y),
                            radius=5,
                            color=(0, 0, 255),
                            thickness=-1,
                        )
                return False

        for target_hsv in self.nearby_object_colors_hsv:
            diff = np.abs(region - target_hsv)
            if np.any(np.all(diff <= [1, 50, 50], axis=-1)):
                return True

        return False

    def process_frame(self, frame):
        """Process each frame to detect and handle objects."""
        contours = self.detect_green_or_blue_objects(frame)
        for contour in contours:
            if cv2.contourArea(contour) < 6:
                continue

            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue

            c_x = int(M["m10"] / M["m00"]) + self.x_root
            c_y = int(M["m01"] // M["m00"]) + self.y_root
            x, y, w, h = cv2.boundingRect(contour)
            if not self.check_color_proximity(frame, (x, y, w, h)):
                if CONFIG.DEBUG:
                    cv2.circle(
                        frame,
                        (c_x, c_y),
                        radius=5,
                        color=CONFIG.YELLOW_COLOR,
                        thickness=-1,
                    )
                continue

            if any(
                math.sqrt((c_x - px) ** 2 + (c_y - py) ** 2) < 35
                for px, py in self.clicked_points
            ):
                if CONFIG.DEBUG:
                    cv2.circle(
                        frame,
                        (c_x, c_y),
                        radius=5,
                        color=CONFIG.ORANGE_COLOR,
                        thickness=-1,
                    )
                continue

            self.clicked_points.append((c_x, c_y))
            if CONFIG.DEBUG:
                cv2.circle(
                    frame, (c_x, c_y), radius=5, color=CONFIG.PINK_COLOR, thickness=-1
                )
            else:
                self.executor.submit(self.click_on_object, c_x, c_y)

        if CONFIG.DEBUG:
            self.draw_and_debug_results(frame, contours)

    def window_monitor(self):
        """Monitor the window and handle play button detection and clicking."""
        try:
            drop_time = 0
            monitor = {
                "top": self.y_root,
                "left": self.x_root,
                "width": self.width_position,
                "height": self.height_position,
            }
            with mss.mss() as sct:
                while True:
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    self.process_frame(frame)
                    play_again_button = self.detect_white_rectangles(frame)
                    if play_again_button:
                        print(
                            "The 'Play' button has been found. It will be clicked in 5 seconds..."
                        )
                        time.sleep(CONFIG.PLAY_BUTTON_WAIT_TIME)
                        c_x, c_y = play_again_button
                        self.click_on_object(c_x + self.x_root, c_y + self.y_root)

                    if drop_time >= CONFIG.MAX_CLICKED_POINTS_CNT:
                        self.clicked_points.clear()
                        drop_time = 0

                    drop_time += 1
                    time.sleep(CONFIG.FRAME_BTW_SLEEP)
        except KeyboardInterrupt:
            print("Process interrupted by user. Exiting...")

        except mss.exception.ScreenShotError:
            print("Make sure app window is not outside of screen")

        except AttributeError as err:
            print(
                f"AttributeError: {err}\n\nMake sure the xwininfo is run currectly(for exmaple don't move until is selector shows)"
            )
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def run(self):
        """Run the Blume application."""
        self.detect_blume_app_position()
        self.window_monitor()


def main():
    Blume().run()


if __name__ == "__main__":
    main()
