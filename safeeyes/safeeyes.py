import atexit
import logging
import os
from threading import Timer
import dbus
import gi
from dbus .mainloop .glib import DBusGMainLoop
from safeeyes import utility
from safeeyes .ui .about_dialog import AboutDialog
from safeeyes .ui .break_screen import BreakScreen
from safeeyes .model import State
from safeeyes .rpc import RPCServer
from safeeyes .plugin_manager import PluginManager
from safeeyes .core import SafeEyesCore
from safeeyes .ui .settings_dialog import SettingsDialog
gi .require_version ('Gtk','3.0')
from gi .repository import Gtk
SAFE_EYES_VERSION ="2.1.6"
class SafeEyes :
    def __init__ (self ,system_locale ,config ):
        self .active =False
        self .break_screen =None
        self .safe_eyes_core =None
        self .config =config
        self .context ={}
        self .plugins_manager =None
        self .settings_dialog_active =False
        self .rpc_server =None
        self ._status =''
        self .context ['version']=SAFE_EYES_VERSION
        self .context ['desktop']=utility .desktop_environment ()
        self .context ['is_wayland']=utility .is_wayland ()
        self .context ['locale']=system_locale
        self .context ['api']={}
        self .context ['api']['show_settings']=lambda :utility .execute_main_thread (
        self .show_settings )
        self .context ['api']['show_about']=lambda :utility .execute_main_thread (
        self .show_about )
        self .context ['api']['enable_safeeyes']=lambda next_break_time =-1 ,reset_breaks =False :utility .execute_main_thread (self .enable_safeeyes ,next_break_time ,reset_breaks )
        self .context ['api']['disable_safeeyes']=lambda status :utility .execute_main_thread (
        self .disable_safeeyes ,status )
        self .context ['api']['status']=self .status
        self .context ['api']['quit']=lambda :utility .execute_main_thread (
        self .quit )
        if self .config .get ('persist_state'):
            self .context ['session']=utility .open_session ()
        else :
            self .context ['session']={'plugin':{}}
        self .break_screen =BreakScreen (
        self .context ,self .on_skipped ,self .on_postponed ,utility .STYLE_SHEET_PATH )
        self .break_screen .initialize (self .config )
        self .plugins_manager =PluginManager ()
        self .safe_eyes_core =SafeEyesCore (self .context )
        self .safe_eyes_core .on_pre_break +=self .plugins_manager .pre_break
        self .safe_eyes_core .on_start_break +=self .on_start_break
        self .safe_eyes_core .start_break +=self .start_break
        self .safe_eyes_core .on_count_down +=self .countdown
        self .safe_eyes_core .on_stop_break +=self .stop_break
        self .safe_eyes_core .on_update_next_break +=self .update_next_break
        self .safe_eyes_core .initialize (self .config )
        self .context ['api']['take_break']=self .take_break
        self .context ['api']['has_breaks']=self .safe_eyes_core .has_breaks
        self .context ['api']['postpone']=self .safe_eyes_core .postpone
        self .context ['api']['get_break_time']=self .safe_eyes_core .get_break_time
        self .plugins_manager .init (self .context ,self .config )
        atexit .register (self .persist_session )
    def start (self ):
        if self .config .get ('use_rpc_server',True ):
            self .__start_rpc_server ()
        if self .safe_eyes_core .has_breaks ():
            self .active =True
            self .context ['state']=State .START
            self .plugins_manager .start ()
            self .safe_eyes_core .start ()
            self .handle_system_suspend ()
    def show_settings (self ):
        if not self .settings_dialog_active :
            logging .info ("Показать диалоговое окно настроек")
            self .settings_dialog_active =True
            settings_dialog =SettingsDialog (
            self .config .clone (),self .save_settings )
            settings_dialog .show ()
    def show_about (self ):
        logging .info ("Показать диалоговое окно «О программе»")
        about_dialog =AboutDialog (SAFE_EYES_VERSION )
        about_dialog .show ()
    def quit (self ):
        logging .info ("Выйти из безопасных глаз")
        self .context ['state']=State .QUIT
        self .plugins_manager .stop ()
        self .safe_eyes_core .stop ()
        self .plugins_manager .exit ()
        self .__stop_rpc_server ()
        self .persist_session ()
        Gtk .main_quit ()
        os ._exit (0 )
    def handle_suspend_callback (self ,sleeping ):
        if sleeping :
            if self .active :
                logging .info ("Остановить Safe Eyes из-за приостановки работы системы")
                self .plugins_manager .stop ()
                self .safe_eyes_core .stop (True )
        else :
            if self .active and self .safe_eyes_core .has_breaks ():
                logging .info ("Возобновить работу Safe Eyes после пробуждения системы")
                self .plugins_manager .start ()
                self .safe_eyes_core .start ()
    def handle_system_suspend (self ):
        DBusGMainLoop (set_as_default =True )
        bus =dbus .SystemBus ()
        bus .add_signal_receiver (self .handle_suspend_callback ,'PrepareForSleep',
        'org.freedesktop.login1.Manager','org.freedesktop.login1')
    def on_skipped (self ):
        logging .info ("Пользователь пропустил перерыв")
        self .safe_eyes_core .skip ()
        self .plugins_manager .stop_break ()
    def on_postponed (self ):
        logging .info ("Пользователь отложил перерыв")
        self .safe_eyes_core .postpone ()
        self .plugins_manager .stop_break ()
    def save_settings (self ,config ):
        self .settings_dialog_active =False
        if self .config ==config :
            return
        logging .info ("Сохранение настроек в Safeeyes.json")
        if self .active :
            self .plugins_manager .stop ()
            self .safe_eyes_core .stop ()
        config .save ()
        self .persist_session ()
        logging .info ("Инициализируйте SafeEyesCore с измененными настройками.")
        if self .rpc_server is None and config .get ('use_rpc_server'):
            self .__start_rpc_server ()
        elif self .rpc_server is not None and not config .get ('use_rpc_server'):
            self .__stop_rpc_server ()
        self .config =config
        self .safe_eyes_core .initialize (config )
        self .break_screen .initialize (config )
        self .plugins_manager .init (self .context ,self .config )
        if self .active and self .safe_eyes_core .has_breaks ():
            Timer (1.0 ,self .safe_eyes_core .start ).start ()
            self .plugins_manager .start ()
    def enable_safeeyes (self ,scheduled_next_break_time =-1 ,reset_breaks =False ):
        if not self .active and self .safe_eyes_core .has_breaks ():
            self .active =True
            self .safe_eyes_core .start (scheduled_next_break_time ,reset_breaks )
            self .plugins_manager .start ()
    def disable_safeeyes (self ,status =None ,is_resting =False ):
        if self .active :
            self .active =False
            self .plugins_manager .stop ()
            self .safe_eyes_core .stop (is_resting )
            if status is None :
                status =_ ('Отключено до перезапуска')
            self ._status =status
    def on_start_break (self ,break_obj ):
        if not self .plugins_manager .start_break (break_obj ):
            return False
        return True
    def start_break (self ,break_obj ):
        widget =self .plugins_manager .get_break_screen_widgets (break_obj )
        actions =self .plugins_manager .get_break_screen_tray_actions (break_obj )
        self .break_screen .show_message (break_obj ,widget ,actions )
    def countdown (self ,countdown ,seconds ):
        self .break_screen .show_count_down (countdown ,seconds )
        self .plugins_manager .countdown (countdown ,seconds )
        return True
    def update_next_break (self ,break_obj ,break_time ):
        self .plugins_manager .update_next_break (break_obj ,break_time )
        self ._status =_ ('Следующий перерыв в %s')%(
        utility .format_time (break_time ))
        if self .config .get ('persist_state'):
            utility .write_json (utility .SESSION_FILE_PATH ,
            self .context ['session'])
    def stop_break (self ):
        self .break_screen .close ()
        self .plugins_manager .stop_break ()
        return True
    def take_break (self ,break_type =None ):
        utility .execute_main_thread (self .safe_eyes_core .take_break ,break_type )
    def status (self ):
        return self ._status
    def persist_session (self ):
        if self .config .get ('persist_state'):
            utility .write_json (utility .SESSION_FILE_PATH ,
            self .context ['session'])
        else :
            utility .delete (utility .SESSION_FILE_PATH )
    def __start_rpc_server (self ):
        if self .rpc_server is None :
            self .rpc_server =RPCServer (self .config .get ('rpc_port'),self .context )
            self .rpc_server .start ()
    def __stop_rpc_server (self ):
        if self .rpc_server is not None :
            self .rpc_server .stop ()
            self .rpc_server =None