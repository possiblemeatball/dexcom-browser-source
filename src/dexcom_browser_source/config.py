from pathlib import Path
import platformdirs


class AppConfig:
    def __init__(self, custom_config_path: Path | None = None):
        self._config_path: Path = custom_config_path if custom_config_path is not None else platformdirs.user_config_path()

        # assume if the config path doesn't exist then this is the first run
        self.first_run: bool = False
        if not self._config_path.exists():
            self.first_run = True