import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import RADIATOR_MODELS
from app.app import replace_variables
print("SUCCESS")
