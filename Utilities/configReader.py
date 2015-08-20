import os

def read():
    """
    This is what grabs all the config info. Returns a dictionary that
    has the different config values in it.
    """
    config_settings = {}
    for var in os.environ.keys():
        if var.starts_with('CFG_'):
            var_name = var.strip('CFG_')
            config_settings[var_name] = os.environ.get(var)
    return config_settings
