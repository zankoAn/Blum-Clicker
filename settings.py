
class Config:
    CLICK_BLUE_OBJECT = True
    MIN_OBJECT_AREA = 100
    MIN_PLAY_AREA = 400
    TPOOL_WORKERS = 40    
    MAX_CLICKED_POINTS_CNT = 5  # Stores clicked points in a list for up to 5 frames (cleared after 5 frames).
    GREEN_OBJ_COLORS = ["#abff61", "#87ff27"]
    BLUE_OBJ_COLORS = ["#82dce9", "#55ccdc"]
    BOMB_COLLORS = ["#9fa19f", "#ddd6d1"]


class ProdConfig(Config):
    DEBUG = False
    FRAME_BTW_SLEEP = 0.09
    PLAY_BUTTON_WAIT_TIME = 5


class DebugConfig(Config):
    DEBUG = True
    FRAME_BTW_SLEEP = 5
    PLAY_BUTTON_WAIT_TIME = 10
    YELLOW_COLOR = (210, 210, 60) # Proximity debug
    ORANGE_COLOR = (210, 120, 60) # Clicked area
    PINK_COLOR = (210, 60, 120) # Center of detected object
    DISPLAY_DELAY_MS = 3000


CONFIG = ProdConfig()
