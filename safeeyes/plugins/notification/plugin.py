import logging
import gi
from safeeyes .model import BreakType
gi .require_version ('Notify','0.7')
from gi .repository import Notify
APPINDICATOR_ID ='safeeyes'
notification =None
context =None
warning_time =10
Notify .init (APPINDICATOR_ID )
def init (ctx ,safeeyes_config ,plugin_config ):
    global context
    global warning_time
    logging .debug ('Инициализировать плагин уведомлений')
    context =ctx
    warning_time =safeeyes_config .get ('pre_break_warning_time')
def on_pre_break (break_obj ):
    global notification
    logging .info ('Показать уведомление')
    message ='\n'
    if break_obj .type ==BreakType .SHORT_BREAK :
        message +=(_ ('Готов к небольшому перерыву через %s секунд.')%warning_time )
    else :
        message +=(_ ('Готов к длительному перерыву через %s секунд.')%warning_time )
    notification =Notify .Notification .new ('Безопасные глаза',message ,icon ='io.github.slgobinath.SafeEyes-enabled')
    try :
        notification .show ()
    except BaseException :
        logging .error ('Не удалось показать уведомление')
def on_start_break (break_obj ):
    global notification
    logging .info ('Закрыть уведомление перед перерывом')
    if notification :
        try :
            notification .close ()
            notification =None
        except BaseException :
            pass
def on_exit ():
    logging .debug ('Плагин стоп-уведомлений')
    Notify .uninit ()