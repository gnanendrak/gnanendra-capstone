from src.pipeline.settings import Settings
from src.pipeline.logging_config import get_logger

settings=Settings()
log=get_logger()
log.info(f'smoke test settings: {settings.model_dump(mode="json")}')
print('OK — settings constructed, log line written')