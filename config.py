class Config:
    """Application Constants and Configuration"""

    DB_PATH = "lged_offline_sync.db"
    PRIMARY_MODEL = "gemini-2.5-flash"
    FALLBACK_MODEL = "gemini-1.5-flash"
    API_TIMEOUT = 30  # seconds
    MAX_IMAGE_SIZE_MB = 10
    RATE_LIMIT_ASSESSMENTS = 10

    # Bangladesh GPS Bounds
    LAT_MIN = 20.5
    LAT_MAX = 26.6
    LON_MIN = 88.0
    LON_MAX = 92.7
