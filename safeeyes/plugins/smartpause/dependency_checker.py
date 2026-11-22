from safeeyes import utility
def validate (plugin_config ,plugin_settings ):
    command =None
    if utility .DESKTOP_ENVIRONMENT =="gnome"and utility .IS_WAYLAND :
        command ="dbus-send"
    elif utility .DESKTOP_ENVIRONMENT =="sway":
        command ="swayidle"
    else :
        command ="xprintidle"
    if not utility .command_exist (command ):
        return _ ("Установите инструмент командной строки «%s».")%command
    else :
        return None