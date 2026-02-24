import sys
from pathlib import Path

# Get project root (one level above tests/)
ROOT = Path(__file__).resolve().parents[1]

# Add project root to Python path
sys.path.insert(0, str(ROOT))