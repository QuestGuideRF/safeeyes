import gi
import logging
import os
from safeeyes import utility
from safeeyes .model import TrayAction
gi .require_version ('Gtk','3.0')
from gi .repository import Gtk
context =None
lock_screen =False
user_locked_screen =False
lock_screen_command =None
min_seconds =0
seconds_passed =0
tray_icon_path =None
def __lock_screen_command ():
    desktop_session =os .environ .get ('DESKTOP_SESSION')
    current_desktop =os .environ .get ('XDG_CURRENT_DESKTOP')
    if desktop_session is not None :
        desktop_session =desktop_session .lower ()
        if ('xfce'in desktop_session or desktop_session .startswith ('xubuntu')or (current_desktop is not None and 'xfce'in current_desktop ))and utility .command_exist ('xflock4'):
            return ['xflock4']
        elif desktop_session =='cinnamon'and utility .command_exist ('cinnamon-screensaver-command'):
            return ['cinnamon-screensaver-command','--lock']
        elif (desktop_session =='pantheon'or desktop_session .startswith ('lubuntu'))and utility .command_exist ('light-locker-command'):
            return ['light-locker-command','--lock']
        elif desktop_session =='mate'and utility .command_exist ('mate-screensaver-command'):
            return ['mate-screensaver-command','--lock']
        elif desktop_session =='kde'or 'plasma'in desktop_session or desktop_session .startswith ('kubuntu')or os .environ .get ('KDE_FULL_SESSION')=='true':
            return ['qdbus','org.freedesktop.ScreenSaver','/ScreenSaver','Lock']
        elif desktop_session in ['gnome','unity','budgie-desktop']or desktop_session .startswith ('ubuntu'):
            if utility .command_exist ('gnome-screensaver-command'):
                return ['gnome-screensaver-command','--lock']
            return ['dbus-send','--type=вызов_метода','--dest=org.gnome.ScreenSaver','/org/gnome/ScreenSaver','org.gnome.ScreenSaver.Lock']
        elif os .environ .get ('GNOME_DESKTOP_SESSION_ID'):
            if 'deprecated'not in os .environ .get ('GNOME_DESKTOP_SESSION_ID')and utility .command_exist ('gnome-screensaver-command'):
                return ['gnome-screensaver-command','--lock']
    return None
def __lock_screen ():
    global user_locked_screen
    user_locked_screen =True
def init (ctx ,safeeyes_config ,plugin_config ):
    global context
    global lock_screen_command
    global min_seconds
    global tray_icon_path
    logging .debug ('Инициализировать плагин скринсейвера')
    context =ctx
    min_seconds =plugin_config ['min_seconds']
    tray_icon_path =os .path .join (plugin_config ['path'],"resource/lock.png")
    if plugin_config ['command']:
        lock_screen_command =plugin_config ['command'].split ()
    else :
        lock_screen_command =__lock_screen_command ()
def on_start_break (break_obj ):
    global lock_screen
    global seconds_passed
    global user_locked_screen
    user_locked_screen =False
    seconds_passed =0
    if lock_screen_command :
        lock_screen =break_obj .is_long_break ()
def on_countdown (countdown ,seconds ):
    global seconds_passed
    seconds_passed =seconds
def on_stop_break ():
    if user_locked_screen or (lock_screen and seconds_passed >=min_seconds ):
        utility .execute_command (lock_screen_command )
def get_tray_action (break_obj ):
    return TrayAction .build ("Экран блокировки",
    tray_icon_path ,
    Gtk .STOCK_DIALOG_AUTHENTICATION ,
    __lock_screen )