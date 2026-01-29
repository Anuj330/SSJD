from dotenv import load_dotenv
load_dotenv()

from app.core.database import Base
from app.models import society, user  # import ALL models here

target_metadata = Base.metadata

