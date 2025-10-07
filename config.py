import yaml

class Config:
    def __init__(self, path="config.yaml"):
        with open(path, "r") as f:
            self._config = yaml.safe_load(f)

    def get(self, *keys, default=None):
        cfg = self._config
        for k in keys:
            if isinstance(cfg, dict) and k in cfg:
                cfg = cfg[k]
            else:
                return default
        return cfg

# bikin instance global
config = Config()
