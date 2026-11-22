from safeeyes import utility
def validate (plugin_config ,plugin_settings ):
    command =None
    if utility .IS_WAYLAND :
        command ="wlrctl"
    else :
        command ="xprop"
    if not utility .command_exist (command ):
        return _ ("Установите инструмент командной строки «%s».")%command
    else :
        return None