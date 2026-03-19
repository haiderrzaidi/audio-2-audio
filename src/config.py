import os
from dotenv import load_dotenv
from utils import get_full_path

# Load variables from .env file
load_dotenv()

class Printable:
    def _get_attributes(self):
        return [
            attr for attr in dir(self)
            if not attr.startswith("__") and not callable(getattr(self, attr))
        ]

    def _get_dict(self):
        attributes = self._get_attributes()
        return {i: getattr(self, i) for i in attributes}

    def __repr__(self):
        return str(self._get_dict())

    def __iter__(self):
        for k, v in self._get_dict().items():
            yield k, v

class Config(Printable):
    # Database Settings
    DB = os.getenv("DB")
    COLLECTION = os.getenv("COLLECTION")
    MONGO_HOST = os.getenv("MONGO_HOST")
    MONGO_USERNAME = os.getenv("MONGO_USERNAME")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
    MONGO_AUTHSOURCE = os.getenv("MONGO_AUTHSOURCE")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE")
    
    # Cache Settings
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    REDIS_PORT = os.getenv("REDIS_PORT")
    
    # AWS Infrastructure
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    INDEX_BUCKET = os.getenv("INDEX_BUCKET")
    
    # AI/ML Endpoints
    AI_URL = os.getenv("AI_URL")
    CLOTH_COUNT_URI = os.getenv("CLOTH_COUNT_URI")
    GENDER_HOST = os.getenv("GENDER_HOST")
    IMAGE_RETRIEVAL_HOST = os.getenv("IMAGE_RETRIEVAL_HOST")
    
    # Model Metadata
    IMAGE_RETRIEVAL_MODELNAME = os.getenv("IMAGE_RETRIEVAL_MODELNAME")
    IMAGE_RETRIEVAL_VERSION = os.getenv("IMAGE_RETRIEVAL_VERSION")
    
    # Hyperparameters (cast to int if present)
    IMAGE_SIZE = int(os.getenv("IMAGE_SIZE", 0))
    EMBEDDING_SIZE = int(os.getenv("EMBEDDING_SIZE", 0))
    CLOSEST_TOP_K = int(os.getenv("CLOSEST_TOP_K", 0))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 0))
    
    # Paths
    INDEX_DIR = get_full_path("../data")