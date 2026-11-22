import os
import logging
import re
import subprocess
import gi
gi .require_version ('Gdk','3.0')
from gi .repository import Gdk
from gi .repository import GdkX11
from safeeyes import utility
context =None
skip_break_window_classes =[]
take_break_window_classes =[]
unfullscreen_allowed =True
dnd_while_on_battery =False
def is_active_window_skipped_wayland (pre_break ):
    cmdlist =['wlrctl','toplevel','find','state:fullscreen']
    try :
        process =subprocess .Popen (cmdlist ,stdout =subprocess .PIPE )
        process .communicate ()[0 ]
        if process .returncode ==0 :
            return True
        elif process .returncode ==1 :
            return False
        elif process .returncode ==127 :
            logging .warning ('Не удалось найти wlrctl, необходимый для обнаружения полноэкранного режима под Wayland.')
            return False
    except subprocess .CalledProcessError :
        logging .warning ('Ошибка поиска полноэкранного приложения')
    return False
def is_active_window_skipped_xorg (pre_break ):
    logging .info ('Поиск полноэкранного приложения')
    screen =Gdk .Screen .get_default ()
    active_window =screen .get_active_window ()
    if active_window :
        active_xid =str (active_window .get_xid ())
        cmdlist =['xprop','-root','-notype','-id',
        active_xid ,'WM_CLASS','_NET_WM_STATE']
        try :
            stdout =subprocess .check_output (cmdlist ).decode ('utf-8')
        except subprocess .CalledProcessError :
            logging .warning ('Ошибка поиска полноэкранного приложения')
        else :
            if stdout :
                is_fullscreen ='FULLSCREEN'in stdout
                process_names =re .findall ('"(.+?)"',stdout )
                if process_names :
                    process_name =process_names [1 ].lower ()
                    if _window_class_matches (process_name ,skip_break_window_classes ):
                        return True
                    elif _window_class_matches (process_name ,take_break_window_classes ):
                        if is_fullscreen and unfullscreen_allowed and not pre_break :
                            try :
                                active_window .unfullscreen ()
                            except BaseException as e :
                                logging .error ('Ошибка при разворачивании окна в полноэкранном режиме '+process_name ,exc_info =e )
                        return False
                return is_fullscreen
    return False
def _window_class_matches (window_class :str ,classes :list )->bool :
    return any (map (lambda w :w in classes ,window_class .split ()))
def is_on_battery ():
    on_battery =False
    available_power_sources =os .listdir ('/sys/class/power_supply')
    logging .info ('Поиск состояния батареи в доступных источниках питания: %s'%str (
    available_power_sources ))
    for power_source in available_power_sources :
        if 'BAT'in power_source :
            battery_status =os .path .join (
            '/sys/class/power_supply',power_source ,'status')
            if os .path .isfile (battery_status ):
                try :
                    with open (battery_status ,'r')as status_file :
                        status =status_file .read ()
                        if status :
                            on_battery ='discharging'in status .lower ()
                except BaseException :
                    logging .error ('Не удалось прочитать %s'%battery_status )
            break
    return on_battery
def init (ctx ,safeeyes_config ,plugin_config ):
    global context
    global skip_break_window_classes
    global take_break_window_classes
    global unfullscreen_allowed
    global dnd_while_on_battery
    logging .debug ('Инициализировать плагин Skip Fullscreen')
    context =ctx
    skip_break_window_classes =_normalize_window_classes (plugin_config ['skip_break_windows'])
    take_break_window_classes =_normalize_window_classes (plugin_config ['take_break_windows'])
    unfullscreen_allowed =plugin_config ['unfullscreen']
    dnd_while_on_battery =plugin_config ['while_on_battery']
def _normalize_window_classes (classes_as_str :str ):
    return [w .lower ()for w in classes_as_str .split ()]
def on_pre_break (break_obj ):
    if utility .IS_WAYLAND :
        skip_break =is_active_window_skipped_wayland (True )
    else :
        skip_break =is_active_window_skipped_xorg (True )
    if dnd_while_on_battery and not skip_break :
        skip_break =is_on_battery ()
    return skip_break
def on_start_break (break_obj ):
    if utility .IS_WAYLAND :
        skip_break =is_active_window_skipped_wayland (True )
    else :
        skip_break =is_active_window_skipped_xorg (True )
    if dnd_while_on_battery and not skip_break :
        skip_break =is_on_battery ()
    return skip_break