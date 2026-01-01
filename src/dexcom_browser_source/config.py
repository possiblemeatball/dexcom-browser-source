from pathlib import Path
import platformdirs
import toml


class AppConfig:
    def __init__(self, custom_config_path: Path | None = None):
        self._config_path: Path = Path(custom_config_path if custom_config_path is not None else platformdirs.user_config_path(), "dexcom-browser-source")
        self._config_file_path: Path = Path(self._config_path, "config.toml")
        self.config: dict[str, dict[str, str | bool | int | float | dict[str, str | bool | int | float | None] | None]] = {
            "app": {
                "metric": False,
            },
            "graph": {
                "last_hours": 24,
                "height_limit": 300,
                "colors": {
                    "appearance": "dark",
                    "hypoglycemia": "red",
                    "hyperglycemia": "yellow",
                    "normal": "grey"
                }
            },
            "dexcom": {
                "hyperglycemia_level": 180,
                "hypoglycemia_level": 70,
                "severe_hypoglycemia_level": 55,
                "account": {
                    "username": None,
                    "password": None,
                },
            }
        }

        # assume if the config file doesn't exist then this is the first run
        self.first_run: bool = False
        if not self._config_path.exists():
            self.first_run = True
            self._config_path.mkdir(parents=True)

        if not self._config_file_path.exists():
            self.first_run = True
        else:
            self.load()

    def load(self):
        self.config = toml.load(f=self._config_file_path)

    def save(self):
        with self._config_file_path.open(mode='w') as f:
            _ = toml.dump(self.config, f)