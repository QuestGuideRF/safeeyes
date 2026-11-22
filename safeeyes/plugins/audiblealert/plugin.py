import logging
from safeeyes import utility
context =None
pre_break_alert =False
post_break_alert =False
def play_sound (resource_name ):
    logging .info ('Воспроизведение звукового оповещения %s',resource_name )
    try :
        path =utility .get_resource_path (resource_name )
        if path is None :
            return
        utility .execute_command ('aplay',['-q',path ])
    except BaseException :
        logging .error ('Не удалось воспроизвести звуковое оповещение %s.',resource_name )
def init (ctx ,safeeyes_config ,plugin_config ):
    global context
    global pre_break_alert
    global post_break_alert
    logging .debug ('Инициализировать плагин Audible Alert')
    context =ctx
    pre_break_alert =plugin_config ['pre_break_alert']
    post_break_alert =plugin_config ['post_break_alert']
def on_pre_break (break_obj ):
    if pre_break_alert :
        play_sound ('on_pre_break.wav')
def on_stop_break ():
    if context ['skipped']or context ['postponed']or not post_break_alert :
        return
    play_sound ('on_stop_break.wav')