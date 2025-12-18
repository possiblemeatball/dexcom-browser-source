from pathlib import Path
import platformdirs
import toml


class AppConfig:
    def __init__(self, custom_config_path: Path | None = None):
        self._config_path: Path = Path(custom_config_path if custom_config_path is not None else platformdirs.user_config_path(), "dexcom-browser-source")
        self.config: dict[str, dict[str, str | int | float | bool | dict[str, str | int | float | bool | None] | None]] = {
            "app": {
                "appearance": "dark",
            },
            "dexcom": {
                "username": "",
                "password": "",
                "metric": False,
                "hypoglycemia_level": 70,
                "hyperglycemia_level": 180,
                "graph_max": 300,
            }
        }

        # assume if the config file doesn't exist then this is the first run
        self.first_run: bool = False
        if not self._config_path.exists():
            self.first_run = True
            self._config_path.mkdir(parents=True)

        self._config_file_path: Path = Path(self._config_path, "config.toml")
        if not self._config_file_path.exists():
            self.first_run = True
        else:
            self.load()

    def load(self):
        self.config = toml.load(f=self._config_file_path)

    def save(self):
        with self._config_file_path.open(mode='w') as f:
            _ = toml.dump(self.config, f)