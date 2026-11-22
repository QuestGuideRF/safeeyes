import logging
import os
import threading
import time
import gi
from safeeyes import utility
from Xlib .display import Display
from Xlib .display import X
gi .require_version ('Gtk','3.0')
from gi .repository import Gdk
from gi .repository import GLib
from gi .repository import Gtk
BREAK_SCREEN_GLADE =os .path .join (utility .BIN_DIRECTORY ,"glade/break_screen.glade")
class BreakScreen :
    def __init__ (self ,context ,on_skipped ,on_postponed ,style_sheet_path ):
        self .context =context
        self .count_labels =[]
        self .display =Display ()
        self .enable_postpone =False
        self .enable_shortcut =False
        self .is_pretified =False
        self .keycode_shortcut_postpone =65
        self .keycode_shortcut_skip =9
        self .on_postponed =on_postponed
        self .on_skipped =on_skipped
        self .shortcut_disable_time =2
        self .strict_break =False
        self .windows =[]
        css_provider =Gtk .CssProvider ()
        css_provider .load_from_path (style_sheet_path )
        Gtk .StyleContext .add_provider_for_screen (Gdk .Screen .get_default (),css_provider ,Gtk .STYLE_PROVIDER_PRIORITY_APPLICATION )
    def initialize (self ,config ):
        logging .info ("Инициализировать экран перерыва")
        self .enable_postpone =config .get ('allow_postpone',False )
        self .keycode_shortcut_postpone =config .get ('shortcut_postpone',65 )
        self .keycode_shortcut_skip =config .get ('shortcut_skip',9 )
        self .shortcut_disable_time =config .get ('shortcut_disable_time',2 )
        self .strict_break =config .get ('strict_break',False )
    def skip_break (self ):
        logging .info ("Пользователь пропустил перерыв")
        self .on_skipped ()
        self .close ()
    def postpone_break (self ):
        logging .info ("Пользователь отложил перерыв")
        self .on_postponed ()
        self .close ()
    def on_window_delete (self ,*args ):
        logging .info ("Закрытие экрана перерыва")
        self .close ()
    def on_skip_clicked (self ,button ):
        self .skip_break ()
    def on_postpone_clicked (self ,button ):
        self .postpone_break ()
    def show_count_down (self ,countdown ,seconds ):
        self .enable_shortcut =self .shortcut_disable_time <=seconds
        mins ,secs =divmod (countdown ,60 )
        timeformat ='{:02d}:{:02d}'.format (mins ,secs )
        GLib .idle_add (lambda :self .__update_count_down (timeformat ))
    def show_message (self ,break_obj ,widget ,tray_actions =[]):
        message =break_obj .name
        image_path =break_obj .image
        self .enable_shortcut =self .shortcut_disable_time <=0
        GLib .idle_add (lambda :self .__show_break_screen (message ,image_path ,widget ,tray_actions ))
    def close (self ):
        logging .info ("Закройте экран(ы) перерыва")
        self .__release_keyboard ()
        GLib .idle_add (lambda :self .__destroy_all_screens ())
    def __tray_action (self ,button ,tray_action ):
        tray_action .reset ()
        tray_action .action ()
    def __show_break_screen (self ,message ,image_path ,widget ,tray_actions ):
        utility .start_thread (self .__lock_keyboard )
        screen =Gtk .Window ().get_screen ()
        no_of_monitors =screen .get_n_monitors ()
        logging .info ("Показывать экраны перерывов на дисплеях %d",no_of_monitors )
        for monitor in range (no_of_monitors ):
            monitor_gemoetry =screen .get_monitor_geometry (monitor )
            x =monitor_gemoetry .x
            y =monitor_gemoetry .y
            builder =Gtk .Builder ()
            builder .add_from_file (BREAK_SCREEN_GLADE )
            builder .connect_signals (self )
            window =builder .get_object ("window_main")
            window .set_title ("SafeEyes-"+str (monitor ))
            lbl_message =builder .get_object ("lbl_message")
            lbl_count =builder .get_object ("lbl_count")
            lbl_widget =builder .get_object ("lbl_widget")
            img_break =builder .get_object ("img_break")
            box_buttons =builder .get_object ("box_buttons")
            toolbar =builder .get_object ("toolbar")
            for tray_action in tray_actions :
                toolbar_button =None
                if tray_action .system_icon :
                    toolbar_button =Gtk .ToolButton .new_from_stock (tray_action .get_icon ())
                else :
                    toolbar_button =Gtk .ToolButton .new (tray_action .get_icon (),tray_action .name )
                tray_action .add_toolbar_button (toolbar_button )
                toolbar_button .connect ("clicked",lambda button ,action :self .__tray_action (button ,action ),tray_action )
                toolbar_button .set_tooltip_text (_ (tray_action .name ))
                toolbar .add (toolbar_button )
                toolbar_button .show ()
            if self .enable_postpone :
                btn_postpone =Gtk .Button (_ ('Postpone'))
                btn_postpone .get_style_context ().add_class ('btn_postpone')
                btn_postpone .connect ('clicked',self .on_postpone_clicked )
                btn_postpone .set_visible (True )
                box_buttons .pack_start (btn_postpone ,True ,True ,0 )
            if not self .strict_break :
                btn_skip =Gtk .Button (_ ('Skip'))
                btn_skip .get_style_context ().add_class ('btn_skip')
                btn_skip .connect ('clicked',self .on_skip_clicked )
                btn_skip .set_visible (True )
                box_buttons .pack_start (btn_skip ,True ,True ,0 )
            if image_path :
                img_break .set_from_file (image_path )
            lbl_message .set_label (message )
            lbl_widget .set_markup (widget )
            self .windows .append (window )
            self .count_labels .append (lbl_count )
            window .set_visual (window .get_screen ().get_rgba_visual ())
            if self .context ['desktop']=='kde':
                window .set_opacity (0.9 )
            window .move (x ,y )
            window .resize (monitor_gemoetry .width ,monitor_gemoetry .height )
            window .stick ()
            window .set_keep_above (True )
            window .fullscreen ()
            window .present ()
            window .move (x ,y )
            window .resize (monitor_gemoetry .width ,monitor_gemoetry .height )
            logging .info ("Экран перерыва перенесен на дисплей[%d, %d]",x ,y )
    def __update_count_down (self ,count ):
        for label in self .count_labels :
            label .set_text (count )
    def __lock_keyboard (self ):
        logging .info ("Блокировка клавиатуры")
        self .lock_keyboard =True
        root =self .display .screen ().root
        root .change_attributes (event_mask =X .KeyPressMask |X .KeyReleaseMask )
        root .grab_keyboard (True ,X .GrabModeAsync ,X .GrabModeAsync ,X .CurrentTime )
        while self .lock_keyboard :
            if self .display .pending_events ()>0 :
                event =self .display .next_event ()
                if self .enable_shortcut and event .type ==X .KeyPress :
                    if event .detail ==self .keycode_shortcut_skip and not self .strict_break :
                        self .skip_break ()
                        break
                    elif self .enable_postpone and event .detail ==self .keycode_shortcut_postpone :
                        self .postpone_break ()
                        break
            else :
                time .sleep (1 )
    def __release_keyboard (self ):
        logging .info ("Разблокировать клавиатуру")
        self .lock_keyboard =False
        self .display .ungrab_keyboard (X .CurrentTime )
        self .display .flush ()
    def __destroy_all_screens (self ):
        for win in self .windows :
            win .destroy ()
        del self .windows [:]
        del self .count_labels [:]