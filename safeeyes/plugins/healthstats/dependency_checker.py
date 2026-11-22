import datetime
from safeeyes import utility
def validate (plugin_config ,plugin_settings ):
    if not utility .module_exist ("croniter"):
        return _ ("Пожалуйста, установите модуль Python «%s».")%"croniter"