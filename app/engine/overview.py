import os
from typing import Optional
import litellm
from dotenv import load_dotenv

from app.api.schemas import AIOverviewPayload, SearchItem
from app.engine.evidence import EvidenceEngine

load_dotenv()


