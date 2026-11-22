import datetime
import logging
import subprocess
import threading
import re
import os
from safeeyes import utility
from safeeyes .model import State
context =None
idle_condition =threading .Condition ()
lock =threading .Lock ()
active =False
idle_time =0
enable_safeeyes =None
disable_safeeyes =None
smart_pause_activated =False
idle_start_time =None
next_break_time =None
next_break_duration =0
short_break_interval =0
waiting_time =2
is_wayland_and_gnome =False
use_swayidle =False
swayidle_process =None
swayidle_lock =threading .Lock ()
swayidle_idle =0
swayidle_active =0
def __swayidle_running ():
    return (swayidle_process is not None and
    swayidle_process .poll ()is None )
def __start_swayidle_monitor ():
    global swayidle_process
    global swayidle_start
    global swayidle_idle
    global swayidle_active
    logging .debug ('Запуск подпроцесса качания')
    swayidle_process =subprocess .Popen ([
    "swayidle","timeout","1","дата +S%s","resume","дата +R%s"
    ],stdout =subprocess .PIPE ,bufsize =1 ,universal_newlines =True ,encoding ='utf-8')
    for line in swayidle_process .stdout :
        with swayidle_lock :
            typ =line [0 ]
            timestamp =int (line [1 :])
            if typ =='S':
                swayidle_idle =timestamp
            elif typ =='R':
                swayidle_active =timestamp
def __stop_swayidle_monitor ():
    if __swayidle_running ():
        logging .debug ('Остановка подпроцесса качания')
        swayidle_process .terminate ()
def __swayidle_idle_time ():
    with swayidle_lock :
        if not __swayidle_running ():
            utility .start_thread (__start_swayidle_monitor )
        if swayidle_idle >swayidle_active :
            idle_time =int (datetime .datetime .now ().timestamp ())-swayidle_idle
            return idle_time
    return 0
def __gnome_wayland_idle_time ():
    try :
        output =subprocess .check_output ([
        'dbus-send',
        '--print-reply',
        '--dest=org.gnome.Mutter.IdleMonitor',
        '/org/gnome/Mutter/IdleMonitor/Core',
        'org.gnome.Mutter.IdleMonitor.GetIdletime'
        ])
        return int (re .search (rb'\d+$',output ).group (0 ))/1000
    except BaseException as e :
        logging .warning ("Не удалось получить время простоя системы для gnome/wayland.")
        logging .warning (str (e ))
        return 0
def __system_idle_time ():
    try :
        if is_wayland_and_gnome :
            return __gnome_wayland_idle_time ()
        elif use_swayidle :
            return __swayidle_idle_time ()
        return int (subprocess .check_output (['xprintidle']).decode ('utf-8'))/1000
    except BaseException :
        return 0
def __is_active ():
    is_active =False
    with lock :
        is_active =active
    return is_active
def __set_active (is_active ):
    global active
    with lock :
        active =is_active
def init (ctx ,safeeyes_config ,plugin_config ):
    global context
    global enable_safeeyes
    global disable_safeeyes
    global postpone
    global idle_time
    global short_break_interval
    global long_break_duration
    global waiting_time
    global postpone_if_active
    global is_wayland_and_gnome
    global use_swayidle
    logging .debug ('Инициализировать плагин Smart Pause')
    context =ctx
    enable_safeeyes =context ['api']['enable_safeeyes']
    disable_safeeyes =context ['api']['disable_safeeyes']
    postpone =context ['api']['postpone']
    idle_time =plugin_config ['idle_time']
    postpone_if_active =plugin_config ['postpone_if_active']
    short_break_interval =safeeyes_config .get (
    'short_break_interval')*60
    long_break_duration =safeeyes_config .get ('long_break_duration')
    waiting_time =min (2 ,idle_time )
    is_wayland_and_gnome =context ['desktop']=='gnome'and context ['is_wayland']
    use_swayidle =context ['desktop']=='sway'
def __start_idle_monitor ():
    global smart_pause_activated
    global idle_start_time
    while __is_active ():
        idle_condition .acquire ()
        idle_condition .wait (waiting_time )
        idle_condition .release ()
        if __is_active ():
            system_idle_time =__system_idle_time ()
            if system_idle_time >=idle_time and context ['state']==State .WAITING :
                smart_pause_activated =True
                idle_start_time =datetime .datetime .now ()-datetime .timedelta (seconds =system_idle_time )
                logging .info ('Приостановить работу Safe Eyes из-за простоя системы')
                disable_safeeyes (None ,True )
            elif system_idle_time <idle_time and context ['state']==State .RESTING and idle_start_time is not None :
                logging .info ('Возобновить работу Safe Eyes из-за активности пользователя')
                smart_pause_activated =False
                idle_period =(datetime .datetime .now ()-idle_start_time )
                idle_seconds =idle_period .total_seconds ()
                context ['idle_period']=idle_seconds
                if idle_seconds <short_break_interval :
                    if next_break_time is not None :
                        next_break =next_break_time +idle_period
                        enable_safeeyes (next_break .timestamp ())
                    else :
                        enable_safeeyes ()
                else :
                    enable_safeeyes ()
def on_start ():
    global active
    if not __is_active ():
        logging .debug ('Запустите плагин умной паузы')
        __set_active (True )
        utility .start_thread (__start_idle_monitor )
def on_stop ():
    global active
    global smart_pause_activated
    if smart_pause_activated :
        smart_pause_activated =False
        return
    logging .debug ('Остановить плагин умной паузы')
    if use_swayidle :
        __stop_swayidle_monitor ()
    __set_active (False )
    idle_condition .acquire ()
    idle_condition .notify_all ()
    idle_condition .release ()
def update_next_break (break_obj ,dateTime ):
    global next_break_time
    global next_break_duration
    next_break_time =dateTime
    next_break_duration =break_obj .duration
def on_start_break (break_obj ):
    if postpone_if_active :
        system_idle_time =__system_idle_time ()
        if system_idle_time <2 :
            postpone (2 )
def disable ():
    context .pop ('idle_period',None )