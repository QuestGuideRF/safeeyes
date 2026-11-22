import datetime
from safeeyes .model import BreakType
import gi
gi .require_version ('Gtk','3.0')
try :
    gi .require_version ('AppIndicator3','0.1')
    from gi .repository import AppIndicator3 as appindicator
except :
    gi .require_version ('AyatanaAppIndicator3','0.1')
    from gi .repository import AyatanaAppIndicator3 as appindicator
from gi .repository import Gtk
import logging
from safeeyes import utility
import threading
import time
APPINDICATOR_ID ='safeeyes_2'
context =None
tray_icon =None
safeeyes_config =None
class TrayIcon :
    def __init__ (self ,context ,plugin_config ):
        self .context =context
        self .on_show_settings =context ['api']['show_settings']
        self .on_show_about =context ['api']['show_about']
        self .quit =context ['api']['quit']
        self .enable_safeeyes =context ['api']['enable_safeeyes']
        self .disable_safeeyes =context ['api']['disable_safeeyes']
        self .take_break =context ['api']['take_break']
        self .has_breaks =context ['api']['has_breaks']
        self .get_break_time =context ['api']['get_break_time']
        self .plugin_config =plugin_config
        self .date_time =None
        self .active =True
        self .wakeup_time =None
        self .idle_condition =threading .Condition ()
        self .lock =threading .Lock ()
        self .allow_disabling =plugin_config ['allow_disabling']
        self .animate =False
        self .indicator =appindicator .Indicator .new (
        APPINDICATOR_ID ,"io.github.slgobinath.SafeEyes-enabled",appindicator .IndicatorCategory .APPLICATION_STATUS )
        self .indicator .set_status (appindicator .IndicatorStatus .ACTIVE )
        self .menu =Gtk .Menu ()
        self .item_info =Gtk .ImageMenuItem ()
        img_timer =Gtk .Image ()
        img_timer .set_from_icon_name ("io.github.slgobinath.SafeEyes-timer",16 )
        self .item_info .set_image (img_timer )
        self .item_separator =Gtk .SeparatorMenuItem ()
        self .item_enable =Gtk .MenuItem ()
        self .item_enable .connect ('activate',self .on_enable_clicked )
        self .item_disable =Gtk .MenuItem ()
        self .sub_menu_disable =Gtk .Menu ()
        self .sub_menu_disable_items =[]
        for disable_option in plugin_config ['disable_options']:
            time_in_minutes =disable_option ['time']
            label =[]
            if not isinstance (time_in_minutes ,int )or time_in_minutes <=0 :
                logging .error ('Недопустимое время в опции отключения: '+str (time_in_minutes ))
                continue
            time_unit =disable_option ['unit'].lower ()
            if time_unit =='seconds'or time_unit =='second':
                time_in_minutes =int (time_in_minutes /60 )
                label =['В течение %d секунды','На %d секунд']
            elif time_unit =='minutes'or time_unit =='minute':
                time_in_minutes =int (time_in_minutes *1 )
                label =['За %d минуту','На %d минут']
            elif time_unit =='hours'or time_unit =='hour':
                time_in_minutes =int (time_in_minutes *60 )
                label =['На %d час','На %d часов']
            else :
                logging .error ('Неверный модуль в опции отключения: '+str (disable_option ))
                continue
            sub_menu_item =Gtk .MenuItem ()
            sub_menu_item .connect ('activate',self .on_disable_clicked ,time_in_minutes )
            self .sub_menu_disable_items .append ([sub_menu_item ,label ,disable_option ['time']])
            self .sub_menu_disable .append (sub_menu_item )
        self .sub_menu_item_until_restart =Gtk .MenuItem ()
        self .sub_menu_item_until_restart .connect ('activate',self .on_disable_clicked ,-1 )
        self .sub_menu_disable .append (self .sub_menu_item_until_restart )
        self .item_disable .set_submenu (self .sub_menu_disable )
        self .item_manual_break =Gtk .MenuItem ()
        self .sub_menu_manual_next_break =Gtk .MenuItem ()
        self .sub_menu_manual_next_break .connect ('activate',self .on_manual_break_clicked ,None )
        self .sub_menu_manual_next_short_break =Gtk .MenuItem ()
        self .sub_menu_manual_next_short_break .connect ('activate',self .on_manual_break_clicked ,BreakType .SHORT_BREAK )
        self .sub_menu_manual_next_long_break =Gtk .MenuItem ()
        self .sub_menu_manual_next_long_break .connect ('activate',self .on_manual_break_clicked ,BreakType .LONG_BREAK )
        self .sub_menu_manual_break =Gtk .Menu ()
        self .sub_menu_manual_break .append (self .sub_menu_manual_next_break )
        self .sub_menu_manual_break .append (self .sub_menu_manual_next_short_break )
        self .sub_menu_manual_break .append (self .sub_menu_manual_next_long_break )
        self .item_manual_break .set_submenu (self .sub_menu_manual_break )
        self .item_settings =Gtk .MenuItem ()
        self .item_settings .connect ('activate',self .show_settings )
        self .item_about =Gtk .MenuItem ()
        self .item_about .connect ('activate',self .show_about )
        self .item_quit =Gtk .MenuItem ()
        self .item_quit .connect ('activate',self .quit_safe_eyes )
        self .set_labels ()
        self .item_enable .set_sensitive (False )
        self .menu .append (self .item_info )
        self .menu .append (self .item_separator )
        self .menu .append (self .item_enable )
        self .menu .append (self .item_disable )
        self .menu .append (self .item_manual_break )
        self .menu .append (self .item_settings )
        self .menu .append (self .item_about )
        self .menu .append (self .item_quit )
        self .menu .show_all ()
        self .item_enable .set_visible (self .allow_disabling )
        self .item_disable .set_visible (self .allow_disabling )
        self .item_quit .set_visible (self .allow_disabling )
        self .item_quit .set_visible (self .allow_disabling )
        self .indicator .set_menu (self .menu )
    def initialize (self ,plugin_config ):
        self .plugin_config =plugin_config
        self .set_labels ()
        self .allow_disabling =plugin_config ['allow_disabling']
        self .item_enable .set_visible (self .allow_disabling )
        self .item_disable .set_visible (self .allow_disabling )
        self .item_quit .set_visible (self .allow_disabling )
        self .item_quit .set_visible (self .allow_disabling )
    def set_labels (self ):
        for entry in self .sub_menu_disable_items :
            entry [0 ].set_label (self .context ['locale'].ngettext (entry [1 ][0 ],entry [1 ][1 ],entry [2 ])%entry [2 ])
        self .sub_menu_item_until_restart .set_label (_ ('До перезапуска'))
        self .item_enable .set_label (_ ('Включить безопасные глаза'))
        self .item_disable .set_label (_ ('Отключить безопасные глаза'))
        breaks_found =self .has_breaks ()
        if breaks_found :
            if self .active :
                if self .date_time :
                    self .__set_next_break_info ()
                self .indicator .set_icon ("io.github.slgobinath.SafeEyes-enabled")
            else :
                if self .wakeup_time :
                    self .item_info .set_label (_ ('Отключено до %s')%utility .format_time (self .wakeup_time ))
                else :
                    self .item_info .set_label (_ ('Отключено до перезапуска'))
                self .indicator .set_label ('','')
                self .indicator .set_icon ("io.github.slgobinath.SafeEyes-disabled")
        else :
            self .item_info .set_label (_ ('Нет доступных перерывов'))
            self .indicator .set_label ('','')
            self .indicator .set_icon ("io.github.slgobinath.SafeEyes-disabled")
        self .item_info .set_sensitive (breaks_found and self .active )
        self .item_enable .set_sensitive (breaks_found and not self .active )
        self .item_disable .set_sensitive (breaks_found and self .active )
        self .item_manual_break .set_sensitive (breaks_found and self .active )
        self .item_manual_break .set_label (_ ('Сделайте перерыв сейчас'))
        self .sub_menu_manual_next_break .set_label (_ ('Любой перерыв'))
        self .sub_menu_manual_next_short_break .set_label (_ ('Короткий перерыв'))
        self .sub_menu_manual_next_long_break .set_label (_ ('Длинный перерыв'))
        self .item_settings .set_label (_ ('Settings'))
        self .item_about .set_label (_ ('About'))
        self .item_quit .set_label (_ ('Quit'))
    def show_icon (self ):
        self .indicator .set_status (appindicator .IndicatorStatus .ACTIVE )
    def hide_icon (self ):
        self .indicator .set_status (appindicator .IndicatorStatus .PASSIVE )
    def quit_safe_eyes (self ,*args ):
        with self .lock :
            self .active =True
            self .idle_condition .acquire ()
            self .idle_condition .notify_all ()
            self .idle_condition .release ()
        self .quit ()
    def show_settings (self ,*args ):
        self .on_show_settings ()
    def show_about (self ,*args ):
        self .on_show_about ()
    def next_break_time (self ,dateTime ):
        logging .info ("Обновить информацию о следующем перерыве")
        self .date_time =dateTime
        self .__set_next_break_info ()
    def __set_next_break_info (self ):
        formatted_time =utility .format_time (self .get_break_time ())
        long_time =self .get_break_time (BreakType .LONG_BREAK )
        if long_time :
            long_time =utility .format_time (long_time )
            if long_time ==formatted_time :
                message =_ ('Следующий длинный перерыв в %s')%(long_time )
            else :
                message =_ ('Следующий перерыв в %s/%s')%(formatted_time ,long_time )
        else :
            message =_ ('Следующий перерыв в %s')%(formatted_time )
        utility .execute_main_thread (self .item_info .set_label ,message )
        if self .plugin_config .get ('show_time_in_tray',False ):
            show_long =long_time and self .plugin_config .get ('show_long_time_in_tray',False )
            self .indicator .set_label (long_time if show_long else formatted_time ,'')
        else :
            self .indicator .set_label ('','')
    def on_manual_break_clicked (self ,*args ):
        if len (args )>1 :
            break_type =args [1 ]
            self .take_break (break_type )
        else :
            self .take_break ()
    def on_enable_clicked (self ,*args ):
        if not self .active :
            with self .lock :
                self .enable_ui ()
                self .enable_safeeyes ()
                self .idle_condition .acquire ()
                self .idle_condition .notify_all ()
                self .idle_condition .release ()
    def on_disable_clicked (self ,*args ):
        if self .active and len (args )>1 :
            self .disable_ui ()
            time_to_wait =args [1 ]
            if time_to_wait <=0 :
                info =_ ('Отключено до перезапуска')
                self .disable_safeeyes (info )
                self .wakeup_time =None
                self .item_info .set_label (info )
            else :
                self .wakeup_time =datetime .datetime .now ()+datetime .timedelta (minutes =time_to_wait )
                info =_ ('Отключено до %s')%utility .format_time (self .wakeup_time )
                self .disable_safeeyes (info )
                self .item_info .set_label (info )
                utility .start_thread (self .__schedule_resume ,time_minutes =time_to_wait )
    def lock_menu (self ):
        if self .active :
            self .menu .set_sensitive (False )
    def unlock_menu (self ):
        if self .active :
            self .menu .set_sensitive (True )
    def disable_ui (self ):
        if self .active :
            logging .info ('Отключить безопасные глаза')
            self .active =False
            self .indicator .set_icon ("io.github.slgobinath.SafeEyes-disabled")
            self .item_info .set_label (_ ('Отключено до перезапуска'))
            self .indicator .set_label ('','')
            self .item_info .set_sensitive (False )
            self .item_enable .set_sensitive (True )
            self .item_disable .set_sensitive (False )
            self .item_manual_break .set_sensitive (False )
    def enable_ui (self ):
        if not self .active :
            logging .info ('Включить безопасные глаза')
            self .active =True
            self .indicator .set_icon ("io.github.slgobinath.SafeEyes-enabled")
            self .item_info .set_sensitive (True )
            self .item_enable .set_sensitive (False )
            self .item_disable .set_sensitive (True )
            self .item_manual_break .set_sensitive (True )
    def __schedule_resume (self ,time_minutes ):
        self .idle_condition .acquire ()
        self .idle_condition .wait (time_minutes *60 )
        self .idle_condition .release ()
        with self .lock :
            if not self .active :
                utility .execute_main_thread (self .item_enable .activate )
    def start_animation (self ):
        if not self .active or not self .animate :
            return
        utility .execute_main_thread (lambda :self .indicator .set_icon ("io.github.slgobinath.SafeEyes-disabled"))
        time .sleep (0.5 )
        utility .execute_main_thread (lambda :self .indicator .set_icon ("io.github.slgobinath.SafeEyes-enabled"))
        if self .animate and self .active :
            time .sleep (0.5 )
            if self .animate and self .active :
                utility .start_thread (self .start_animation )
    def stop_animation (self ):
        self .animate =False
        if self .active :
            utility .execute_main_thread (lambda :self .indicator .set_icon ("io.github.slgobinath.SafeEyes-enabled"))
        else :
            utility .execute_main_thread (lambda :self .indicator .set_icon ("io.github.slgobinath.SafeEyes-disabled"))
def init (ctx ,safeeyes_cfg ,plugin_config ):
    global context
    global tray_icon
    global safeeyes_config
    logging .debug ('Инициализировать плагин значка в трее')
    context =ctx
    safeeyes_config =safeeyes_cfg
    if not tray_icon :
        tray_icon =TrayIcon (context ,plugin_config )
    else :
        tray_icon .initialize (plugin_config )
def update_next_break (break_obj ,next_break_time ):
    tray_icon .next_break_time (next_break_time )
def on_pre_break (break_obj ):
    if safeeyes_config .get ('strict_break'):
        tray_icon .lock_menu ()
    tray_icon .animate =True
    tray_icon .start_animation ()
def on_start_break (break_obj ):
    tray_icon .stop_animation ()
def on_stop_break ():
    tray_icon .unlock_menu ()
def on_start ():
    tray_icon .enable_ui ()
def on_stop ():
    tray_icon .disable_ui ()