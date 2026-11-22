import importlib
import logging
import os
import sys
from safeeyes import utility
sys .path .append (os .path .abspath (utility .SYSTEM_PLUGINS_DIR ))
sys .path .append (os .path .abspath (utility .USER_PLUGINS_DIR ))
HORIZONTAL_LINE_LENGTH =64
class PluginManager :
    def __init__ (self ):
        logging .info ('Загрузите все плагины')
        self .__plugins ={}
        self .__plugins_on_init =[]
        self .__plugins_on_start =[]
        self .__plugins_on_stop =[]
        self .__plugins_on_exit =[]
        self .__plugins_on_pre_break =[]
        self .__plugins_on_start_break =[]
        self .__plugins_on_stop_break =[]
        self .__plugins_on_countdown =[]
        self .__plugins_update_next_break =[]
        self .__widget_plugins =[]
        self .__tray_actions_plugins =[]
        self .last_break =None
        self .horizontal_line ='─'*HORIZONTAL_LINE_LENGTH
    def init (self ,context ,config ):
        for plugin in config .get ('plugins'):
            try :
                self .__load_plugin (plugin )
            except BaseException as e :
                traceback_wanted =logging .getLogger ().getEffectiveLevel ()==logging .DEBUG
                if traceback_wanted :
                    import traceback
                    traceback .print_exc ()
                logging .error ('Ошибка при загрузке плагина %s: %s.',plugin ['id'],e )
                continue
        for plugin in self .__plugins_on_init :
            plugin ['module'].init (context ,config ,plugin ['config'])
        return True
    def start (self ):
        for plugin in self .__plugins_on_start :
            plugin ['module'].on_start ()
        return True
    def stop (self ):
        for plugin in self .__plugins_on_stop :
            plugin ['module'].on_stop ()
        return True
    def exit (self ):
        for plugin in self .__plugins_on_exit :
            plugin ['module'].on_exit ()
        return True
    def pre_break (self ,break_obj ):
        for plugin in self .__plugins_on_pre_break :
            if break_obj .plugin_enabled (plugin ['id'],plugin ['enabled']):
                if plugin ['module'].on_pre_break (break_obj ):
                    return False
        return True
    def start_break (self ,break_obj ):
        self .last_break =break_obj
        for plugin in self .__plugins_on_start_break :
            if break_obj .plugin_enabled (plugin ['id'],plugin ['enabled']):
                if plugin ['module'].on_start_break (break_obj ):
                    return False
        return True
    def stop_break (self ):
        for plugin in self .__plugins_on_stop_break :
            if self .last_break .plugin_enabled (plugin ['id'],plugin ['enabled']):
                plugin ['module'].on_stop_break ()
    def countdown (self ,countdown ,seconds ):
        for plugin in self .__plugins_on_countdown :
            if self .last_break .plugin_enabled (plugin ['id'],plugin ['enabled']):
                plugin ['module'].on_countdown (countdown ,seconds )
    def update_next_break (self ,break_obj ,break_time ):
        for plugin in self .__plugins_update_next_break :
            plugin ['module'].update_next_break (break_obj ,break_time )
        return True
    def get_break_screen_widgets (self ,break_obj ):
        widget =''
        for plugin in self .__widget_plugins :
            if break_obj .plugin_enabled (plugin ['id'],plugin ['enabled']):
                try :
                    title =plugin ['module'].get_widget_title (break_obj ).upper ().strip ()
                    if title =='':
                        continue
                    content =plugin ['module'].get_widget_content (break_obj )
                    if content =='':
                        continue
                    widget +='<b>{}</b>\n{}\n{}\n\n\n'.format (title ,self .horizontal_line ,content )
                except BaseException :
                    continue
        return widget .strip ()
    def get_break_screen_tray_actions (self ,break_obj ):
        actions =[]
        for plugin in self .__tray_actions_plugins :
            if break_obj .plugin_enabled (plugin ['id'],plugin ['enabled']):
                action =plugin ['module'].get_tray_action (break_obj )
                if action :
                    actions .append (action )
        return actions
    def __load_plugin (self ,plugin ):
        plugin_enabled =plugin ['enabled']
        if plugin ['id']in self .__plugins and not plugin_enabled :
            plugin_obj =self .__plugins [plugin ['id']]
            if plugin_obj ['enabled']:
                plugin_obj ['enabled']=False
                utility .remove_if_exists (self .__plugins_on_start ,plugin_obj )
                utility .remove_if_exists (self .__plugins_on_stop ,plugin_obj )
                utility .remove_if_exists (self .__plugins_on_exit ,plugin_obj )
                utility .remove_if_exists (self .__plugins_update_next_break ,plugin_obj )
                if utility .has_method (plugin_obj ['module'],'disable'):
                    plugin_obj ['module'].disable ()
                logging .info ("Плагин «%s» успешно выгружен.",plugin ['id'])
            if not plugin_obj ['break_override_allowed']:
                utility .remove_if_exists (self .__plugins_on_init ,plugin_obj )
                utility .remove_if_exists (self .__plugins_on_pre_break ,plugin_obj )
                utility .remove_if_exists (self .__plugins_on_start_break ,plugin_obj )
                utility .remove_if_exists (self .__plugins_on_stop_break ,plugin_obj )
                utility .remove_if_exists (self .__plugins_on_countdown ,plugin_obj )
                utility .remove_if_exists (self .__widget_plugins ,plugin_obj )
                utility .remove_if_exists (self .__tray_actions_plugins ,plugin_obj )
                del self .__plugins [plugin ['id']]
            return
        if os .path .isfile (os .path .join (utility .SYSTEM_PLUGINS_DIR ,plugin ['id'],'plugin.py')):
            plugin_dir =utility .SYSTEM_PLUGINS_DIR
        elif os .path .isfile (os .path .join (utility .USER_PLUGINS_DIR ,plugin ['id'],'plugin.py')):
            plugin_dir =utility .USER_PLUGINS_DIR
        else :
            logging .error ('Plugin.py не найден для плагина: %s',plugin ['id'])
            return
        plugin_path =os .path .join (plugin_dir ,plugin ['id'])
        plugin_config_path =os .path .join (plugin_path ,'config.json')
        if not os .path .isfile (plugin_config_path ):
            logging .error ('config.json не найден для плагина: %s',plugin ['id'])
            return
        plugin_config =utility .load_json (plugin_config_path )
        if plugin_config is None :
            return
        if plugin_enabled or plugin_config .get ('break_override_allowed',False ):
            if plugin ['id']in self .__plugins :
                if utility .check_plugin_dependencies (plugin ['id'],plugin_config ,plugin .get ('settings',{}),plugin_path ):
                    plugin_obj ['enabled']=False
                    utility .remove_if_exists (self .__plugins_on_start ,plugin_obj )
                    utility .remove_if_exists (self .__plugins_on_stop ,plugin_obj )
                    utility .remove_if_exists (self .__plugins_on_exit ,plugin_obj )
                    utility .remove_if_exists (self .__plugins_update_next_break ,plugin_obj )
                    utility .remove_if_exists (self .__plugins_on_init ,plugin_obj )
                    utility .remove_if_exists (self .__plugins_on_pre_break ,plugin_obj )
                    utility .remove_if_exists (self .__plugins_on_start_break ,plugin_obj )
                    utility .remove_if_exists (self .__plugins_on_stop_break ,plugin_obj )
                    utility .remove_if_exists (self .__plugins_on_countdown ,plugin_obj )
                    utility .remove_if_exists (self .__widget_plugins ,plugin_obj )
                    utility .remove_if_exists (self .__tray_actions_plugins ,plugin_obj )
                    del self .__plugins [plugin ['id']]
                plugin_obj =self .__plugins [plugin ['id']]
                plugin_obj ['config']=dict (plugin .get ('settings',{}))
                plugin_obj ['config']['path']=os .path .join (plugin_dir ,plugin ['id'])
                if plugin_obj ['enabled']:
                    return
                if plugin_enabled :
                    plugin_obj ['enabled']=True
                    module =plugin_obj ['module']
                    self .__init_plugin (module ,plugin_obj )
            else :
                if utility .check_plugin_dependencies (plugin ['id'],plugin_config ,plugin .get ('settings',{}),plugin_path ):
                    return
                module =importlib .import_module ((plugin ['id']+'.plugin'))
                logging .info ("%s успешно загружен",str (module ))
                plugin_obj ={'id':plugin ['id'],'module':module ,'config':dict (plugin .get (
                'settings',{})),'enabled':plugin_enabled ,
                'break_override_allowed':plugin_config .get ('break_override_allowed',False )}
                plugin_obj ['config']['path']=os .path .join (plugin_dir ,plugin ['id'])
                self .__plugins [plugin ['id']]=plugin_obj
                if utility .has_method (module ,'enable'):
                    module .enable ()
                if plugin_enabled :
                    self .__init_plugin (module ,plugin_obj )
                if utility .has_method (module ,'init',3 ):
                    self .__plugins_on_init .append (plugin_obj )
                if utility .has_method (module ,'on_pre_break',1 ):
                    self .__plugins_on_pre_break .append (plugin_obj )
                if utility .has_method (module ,'on_start_break',1 ):
                    self .__plugins_on_start_break .append (plugin_obj )
                if utility .has_method (module ,'on_stop_break',0 ):
                    self .__plugins_on_stop_break .append (plugin_obj )
                if utility .has_method (module ,'on_countdown',2 ):
                    self .__plugins_on_countdown .append (plugin_obj )
                if utility .has_method (module ,'get_widget_title',1 )and utility .has_method (module ,
                'get_widget_content',1 ):
                    self .__widget_plugins .append (plugin_obj )
                if utility .has_method (module ,'get_tray_action',1 ):
                    self .__tray_actions_plugins .append (plugin_obj )
    def __init_plugin (self ,module ,plugin_obj ):
        if utility .has_method (module ,'on_start'):
            self .__plugins_on_start .append (plugin_obj )
        if utility .has_method (module ,'on_stop'):
            self .__plugins_on_stop .append (plugin_obj )
        if utility .has_method (module ,'on_exit'):
            self .__plugins_on_exit .append (plugin_obj )
        if utility .has_method (module ,'update_next_break',2 ):
            self .__plugins_update_next_break .append (plugin_obj )