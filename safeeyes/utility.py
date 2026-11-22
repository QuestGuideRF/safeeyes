import errno
import inspect
import importlib
import json
import locale
import logging
import os
import re
import sys
import shutil
import subprocess
import threading
from distutils .version import LooseVersion
from logging .handlers import RotatingFileHandler
from pathlib import Path
import babel .core
import babel .dates
import gi
gi .require_version ('Gtk','3.0')
from gi .repository import Gtk
from gi .repository import GLib
from gi .repository import GdkPixbuf
gi .require_version ('Gdk','3.0')
BIN_DIRECTORY =os .path .dirname (os .path .realpath (__file__ ))
HOME_DIRECTORY =os .environ .get ('HOME')or os .path .expanduser ('~')
CONFIG_DIRECTORY =os .path .join (os .environ .get (
'XDG_CONFIG_HOME')or os .path .join (HOME_DIRECTORY ,'.config'),'safeeyes')
STYLE_SHEET_DIRECTORY =os .path .join (CONFIG_DIRECTORY ,'style')
CONFIG_FILE_PATH =os .path .join (CONFIG_DIRECTORY ,'safeeyes.json')
CONFIG_RESOURCE =os .path .join (CONFIG_DIRECTORY ,'resource')
SESSION_FILE_PATH =os .path .join (CONFIG_DIRECTORY ,'session.json')
STYLE_SHEET_PATH =os .path .join (STYLE_SHEET_DIRECTORY ,'safeeyes_style.css')
SYSTEM_CONFIG_FILE_PATH =os .path .join (BIN_DIRECTORY ,"config/safeeyes.json")
SYSTEM_STYLE_SHEET_PATH =os .path .join (
BIN_DIRECTORY ,"config/style/safeeyes_style.css")
LOG_FILE_PATH =os .path .join (HOME_DIRECTORY ,'safeeyes.log')
SYSTEM_PLUGINS_DIR =os .path .join (BIN_DIRECTORY ,'plugins')
USER_PLUGINS_DIR =os .path .join (CONFIG_DIRECTORY ,'plugins')
LOCALE_PATH =os .path .join (BIN_DIRECTORY ,'config/locale')
SYSTEM_DESKTOP_FILE =os .path .join (BIN_DIRECTORY ,"platform/io.github.slgobinath.SafeEyes.desktop")
SYSTEM_ICONS =os .path .join (BIN_DIRECTORY ,"platform/icons")
DESKTOP_ENVIRONMENT =None
IS_WAYLAND =False
def get_resource_path (resource_name ):
    if resource_name is None :
        return None
    resource_location =os .path .join (CONFIG_RESOURCE ,resource_name )
    if not os .path .isfile (resource_location ):
        resource_location =os .path .join (
        BIN_DIRECTORY ,'resource',resource_name )
        if not os .path .isfile (resource_location ):
            resource_location =None
    return resource_location
def start_thread (target_function ,**args ):
    thread =threading .Thread (target =target_function ,name ="WorkThread",daemon =False ,kwargs =args )
    thread .start ()
def execute_main_thread (target_function ,arg1 =None ,arg2 =None ):
    if arg1 is not None and arg2 is not None :
        GLib .idle_add (lambda :target_function (arg1 ,arg2 ))
    elif arg1 is not None :
        GLib .idle_add (lambda :target_function (arg1 ))
    elif arg2 is not None :
        GLib .idle_add (lambda :target_function (arg2 ))
    else :
        GLib .idle_add (target_function )
def system_locale (category =locale .LC_MESSAGES ):
    try :
        locale .setlocale (locale .LC_ALL ,'')
        sys_locale =locale .getlocale (category )[0 ]
        if not sys_locale :
            sys_locale ='en_US.UTF-8'
        return sys_locale
    except BaseException :
        return 'en_US.UTF-8'
def format_time (time ):
    sys_locale =system_locale (locale .LC_TIME )
    try :
        return babel .dates .format_time (time ,format ='short',locale =sys_locale )
    except babel .core .UnknownLocaleError :
        return babel .dates .format_time (time ,format ='short',locale ='en')
def mkdir (path ):
    try :
        os .makedirs (path )
    except OSError as exc :
        if exc .errno ==errno .EEXIST and os .path .isdir (path ):
            pass
        else :
            logging .error ('Ошибка при создании '+str (path ))
            raise
def load_json (json_path ):
    json_obj =None
    if os .path .isfile (json_path ):
        try :
            with open (json_path )as config_file :
                json_obj =json .load (config_file )
        except BaseException :
            pass
    return json_obj
def write_json (json_path ,json_obj ):
    try :
        with open (json_path ,'w')as json_file :
            json .dump (json_obj ,json_file ,indent =4 ,sort_keys =True )
    except BaseException :
        pass
def delete (file_path ):
    try :
        os .remove (file_path )
    except OSError :
        pass
def check_plugin_dependencies (plugin_id ,plugin_config ,plugin_settings ,plugin_path ):
    if plugin_config ['dependencies']['desktop_environments']:
        if DESKTOP_ENVIRONMENT not in plugin_config ['dependencies']['desktop_environments']:
            return _ ('Плагин не поддерживает среду рабочего стола %s.')%DESKTOP_ENVIRONMENT
    for module in plugin_config ['dependencies']['python_modules']:
        if not module_exist (module ):
            return _ ("Пожалуйста, установите модуль Python «%s».")%module
    for command in plugin_config ['dependencies']['shell_commands']:
        if not command_exist (command ):
            return _ ("Установите инструмент командной строки «%s».")%command
    for resource in plugin_config ['dependencies']['resources']:
        if get_resource_path (resource )is None :
            return _ ('Добавьте ресурс %(resource)s в каталог %(config_resource)s.')%{'resource':resource ,'config_resource':CONFIG_RESOURCE }
    plugin_dependency_checker =os .path .join (plugin_path ,'dependency_checker.py')
    if os .path .isfile (plugin_dependency_checker ):
        dependency_checker =importlib .import_module ((plugin_id +'.dependency_checker'))
        if dependency_checker and hasattr (dependency_checker ,"validate"):
            return dependency_checker .validate (plugin_config ,plugin_settings )
    return None
def load_plugins_config (safeeyes_config ):
    configs =[]
    for plugin in safeeyes_config .get ('plugins'):
        plugin_path =os .path .join (SYSTEM_PLUGINS_DIR ,plugin ['id'])
        if not os .path .isdir (plugin_path ):
            plugin_path =os .path .join (USER_PLUGINS_DIR ,plugin ['id'])
        plugin_config_path =os .path .join (plugin_path ,'config.json')
        plugin_icon_path =os .path .join (plugin_path ,'icon.png')
        plugin_module_path =os .path .join (plugin_path ,'plugin.py')
        if not os .path .isfile (plugin_module_path ):
            return
        icon =None
        if os .path .isfile (plugin_icon_path ):
            icon =plugin_icon_path
        else :
            icon =get_resource_path ('ic_plugin.png')
        config =load_json (plugin_config_path )
        if config is None :
            continue
        dependency_description =check_plugin_dependencies (plugin ['id'],config ,plugin .get ('settings',{}),plugin_path )
        if dependency_description :
            plugin ['enabled']=False
            config ['error']=True
            config ['meta']['description']=dependency_description
            icon =get_resource_path ('ic_warning.png')
        else :
            config ['error']=False
        config ['id']=plugin ['id']
        config ['icon']=icon
        config ['enabled']=plugin ['enabled']
        for setting in config ['settings']:
            setting ['safeeyes_config']=plugin ['settings']
        configs .append (config )
    return configs
def desktop_environment ():
    global DESKTOP_ENVIRONMENT
    desktop_session =os .environ .get ('DESKTOP_SESSION')
    current_desktop =os .environ .get ('XDG_CURRENT_DESKTOP')
    env ='unknown'
    if desktop_session is not None :
        desktop_session =desktop_session .lower ()
        if desktop_session in ['gnome','unity','budgie-desktop','cinnamon','mate','xfce4','lxde','pantheon','fluxbox','blackbox','openbox','icewm','jwm','afterstep','trinity','kde']:
            env =desktop_session
        elif desktop_session .startswith ('xubuntu')or (current_desktop is not None and 'xfce'in current_desktop ):
            env ='xfce'
        elif desktop_session .startswith ('lubuntu'):
            env ='lxde'
        elif 'plasma'in desktop_session or desktop_session .startswith ('kubuntu')or os .environ .get ('KDE_FULL_SESSION')=='true':
            env ='kde'
        elif os .environ .get ('GNOME_DESKTOP_SESSION_ID'):
            env ='gnome'
        elif desktop_session .startswith ('ubuntu'):
            env ='unity'
    elif current_desktop is not None :
        if current_desktop .startswith ('sway'):
            env ='sway'
    DESKTOP_ENVIRONMENT =env
    return env
def is_wayland ():
    global IS_WAYLAND
    if "WAYLAND_DISPLAY"in os .environ :
        IS_WAYLAND =True
        return IS_WAYLAND
    try :
        session_id =subprocess .check_output (['loginctl']).split (b'\n')[1 ].split ()[0 ]
        output =subprocess .check_output (
        ['loginctl','show-session',session_id ,'-p','Type']
        )
    except BaseException :
        logging .warning ('Невозможно определить, работает ли Wayland. Предполагая, что нет.')
        IS_WAYLAND =False
    else :
        IS_WAYLAND =bool (re .search (b'wayland',output ,re .IGNORECASE ))
    return IS_WAYLAND
def execute_command (command ,args =[]):
    if command :
        command_to_execute =[]
        if isinstance (command ,str ):
            command_to_execute .append (command )
        else :
            command_to_execute .extend (command )
        if args :
            command_to_execute .extend (args )
        try :
            subprocess .Popen (command_to_execute )
        except BaseException :
            logging .error ('Ошибка при выполнении команды '+str (command ))
def command_exist (command ):
    if shutil .which (command ):
        return True
    return False
def module_exist (module ):
    try :
        importlib .util .find_spec (module )
        return True
    except ImportError :
        return False
def merge_configs (new_config ,old_config ):
    new_config =new_config .copy ()
    new_config .update (old_config )
    return new_config
def initialize_safeeyes ():
    logging .info ('Скопируйте файлы конфигурации в XDG_CONFIG_HOME(или ~/.config)/safeeyes.')
    delete (CONFIG_FILE_PATH )
    mkdir (STYLE_SHEET_DIRECTORY )
    shutil .copy2 (SYSTEM_CONFIG_FILE_PATH ,CONFIG_FILE_PATH )
    os .chmod (CONFIG_FILE_PATH ,0o777 )
    if not os .path .isfile (STYLE_SHEET_PATH ):
        shutil .copy2 (SYSTEM_STYLE_SHEET_PATH ,STYLE_SHEET_PATH )
        os .chmod (STYLE_SHEET_PATH ,0o777 )
    create_startup_entry (force =True )
def create_startup_entry (force =False ):
    startup_dir_path =os .path .join (HOME_DIRECTORY ,'.config/autostart')
    startup_entry =os .path .join (startup_dir_path ,'io.github.slgobinath.SafeEyes.desktop')
    obsolete_entry =os .path .join (startup_dir_path ,'safeeyes.desktop')
    create_link =False
    if force :
        create_link =True
    else :
        if os .path .islink (startup_entry ):
            try :
                os .stat (startup_entry )
            except FileNotFoundError :
                create_link =True
        if os .path .islink (obsolete_entry ):
            create_link =True
            delete (obsolete_entry )
    if create_link :
        mkdir (startup_dir_path )
        delete (startup_entry )
        try :
            os .symlink (SYSTEM_DESKTOP_FILE ,startup_entry )
        except OSError :
            logging .error ("Не удалось создать запись запуска в %s."%startup_entry )
def initialize_platform ():
    logging .debug ("Инициализировать платформу")
    applications_dir_path =os .path .join (HOME_DIRECTORY ,'.local/share/applications')
    icons_dir_path =os .path .join (HOME_DIRECTORY ,'.local/share/icons')
    desktop_entry =os .path .join (applications_dir_path ,'io.github.slgobinath.SafeEyes.desktop')
    mkdir (icons_dir_path )
    if not os .path .exists (os .path .join (sys .prefix ,"share/applications/io.github.slgobinath.SafeEyes.desktop")):
        mkdir (applications_dir_path )
        delete (desktop_entry )
        try :
            os .symlink (SYSTEM_DESKTOP_FILE ,desktop_entry )
        except OSError :
            logging .error ("Не удалось создать запись на рабочем столе в %s."%desktop_entry )
    for (path ,_ ,filenames )in os .walk (SYSTEM_ICONS ):
        for filename in filenames :
            system_icon =os .path .join (path ,filename )
            local_icon =os .path .join (icons_dir_path ,os .path .relpath (system_icon ,SYSTEM_ICONS ))
            global_icon =os .path .join (sys .prefix ,"share/icons",os .path .relpath (system_icon ,SYSTEM_ICONS ))
            parent_dir =str (Path (local_icon ).parent )
            if os .path .exists (global_icon ):
                continue
            mkdir (parent_dir )
            delete (local_icon )
            try :
                os .symlink (system_icon ,local_icon )
            except OSError :
                logging .error ("Не удалось создать ссылку на значок в %s."%local_icon )
def reset_config ():
    delete (CONFIG_FILE_PATH )
    delete (STYLE_SHEET_PATH )
    shutil .copy2 (SYSTEM_CONFIG_FILE_PATH ,CONFIG_FILE_PATH )
    shutil .copy2 (SYSTEM_STYLE_SHEET_PATH ,STYLE_SHEET_PATH )
    os .chmod (CONFIG_FILE_PATH ,0o777 )
    os .chmod (STYLE_SHEET_PATH ,0o777 )
    create_startup_entry ()
def replace_style_sheet ():
    delete (STYLE_SHEET_PATH )
    shutil .copy2 (SYSTEM_STYLE_SHEET_PATH ,STYLE_SHEET_PATH )
    os .chmod (STYLE_SHEET_PATH ,0o777 )
def initialize_logging (debug ):
    root_logger =logging .getLogger ()
    log_formatter =logging .Formatter (
    '%(asctime)s [%(имя уровня)s]:[%(имя потока)s] %(сообщение)s')
    if debug :
        file_handler =RotatingFileHandler (
        LOG_FILE_PATH ,maxBytes =1024 *1024 ,backupCount =5 ,encoding =None ,delay =0 )
        file_handler .setFormatter (log_formatter )
        console_handler =logging .StreamHandler ()
        console_handler .setFormatter (log_formatter )
        root_logger .setLevel (logging .DEBUG )
        root_logger .addHandler (console_handler )
        root_logger .addHandler (file_handler )
    else :
        root_logger .propagate =False
def __open_plugin_config (plugins_dir ,plugin_id ):
    plugin_config_path =os .path .join (plugins_dir ,plugin_id ,'config.json')
    plugin_module_path =os .path .join (plugins_dir ,plugin_id ,'plugin.py')
    if not os .path .isfile (plugin_config_path )or not os .path .isfile (plugin_module_path ):
        return None
    return load_json (plugin_config_path )
def __update_plugin_config (plugin ,plugin_config ,config ):
    if plugin_config is None :
        config ['plugins'].remove (plugin )
    else :
        if LooseVersion (plugin .get ('version','0.0.0'))!=LooseVersion (plugin_config ['meta']['version']):
            plugin ['version']=plugin_config ['meta']['version']
            setting_ids =[]
            for setting in plugin_config ['settings']:
                setting_ids .append (setting ['id'])
                if 'settings'not in plugin :
                    plugin ['settings']={}
                if plugin ['settings'].get (setting ['id'],None )is None :
                    plugin ['settings'][setting ['id']]=setting ['default']
            keys_to_remove =[]
            for key in plugin .get ('settings',[]):
                if key not in setting_ids :
                    keys_to_remove .append (key )
            for key in keys_to_remove :
                del plugin ['settings'][key ]
def __add_plugin_config (plugin_id ,plugin_config ,safe_eyes_config ):
    if plugin_config is None :
        return
    config ={}
    config ['id']=plugin_id
    config ['enabled']=False
    config ['version']=plugin_config ['meta']['version']
    if plugin_config ['settings']:
        config ['settings']={}
        for setting in plugin_config ['settings']:
            config ['settings'][setting ['id']]=setting ['default']
    safe_eyes_config ['plugins'].append (config )
def merge_plugins (config ):
    system_plugins =None
    user_plugins =None
    if os .path .isdir (SYSTEM_PLUGINS_DIR ):
        system_plugins =os .listdir (SYSTEM_PLUGINS_DIR )
    else :
        system_plugins =[]
    if os .path .isdir (USER_PLUGINS_DIR ):
        user_plugins =os .listdir (USER_PLUGINS_DIR )
    else :
        user_plugins =[]
    for plugin in config ['plugins']:
        plugin_id =plugin ['id']
        if plugin_id in system_plugins :
            plugin_config =__open_plugin_config (SYSTEM_PLUGINS_DIR ,plugin_id )
            __update_plugin_config (plugin ,plugin_config ,config )
            system_plugins .remove (plugin_id )
        elif plugin_id in user_plugins :
            plugin_config =__open_plugin_config (USER_PLUGINS_DIR ,plugin_id )
            __update_plugin_config (plugin ,plugin_config ,config )
            user_plugins .remove (plugin_id )
        else :
            config ['plugins'].remove (plugin )
    for plugin_id in system_plugins :
        plugin_config =__open_plugin_config (SYSTEM_PLUGINS_DIR ,plugin_id )
        __add_plugin_config (plugin_id ,plugin_config ,config )
    for plugin_id in user_plugins :
        plugin_config =__open_plugin_config (USER_PLUGINS_DIR ,plugin_id )
        __add_plugin_config (plugin_id ,plugin_config ,config )
def open_session ():
    logging .info ('Чтение файла сеанса')
    session =load_json (SESSION_FILE_PATH )
    if session is None :
        session ={'plugin':{}}
    return session
def create_gtk_builder (glade_file ):
    builder =Gtk .Builder ()
    builder .set_translation_domain ('safeeyes')
    builder .add_from_file (glade_file )
    for obj in builder .get_objects ():
        if (not isinstance (obj ,Gtk .SeparatorMenuItem ))and hasattr (obj ,"get_label"):
            label =obj .get_label ()
            if label is not None :
                obj .set_label (_ (label ))
        elif hasattr (obj ,"get_title"):
            title =obj .get_title ()
            if title is not None :
                obj .set_title (_ (title ))
    return builder
def load_and_scale_image (path ,width ,height ):
    if not os .path .isfile (path ):
        return None
    pixbuf =GdkPixbuf .Pixbuf .new_from_file_at_scale (
    filename =path ,
    width =width ,
    height =height ,
    preserve_aspect_ratio =True )
    image =Gtk .Image .new_from_pixbuf (pixbuf )
    return image
def has_method (module ,method_name ,no_of_args =0 ):
    if hasattr (module ,method_name ):
        if len (inspect .getfullargspec (getattr (module ,method_name )).args )==no_of_args :
            return True
    return False
def remove_if_exists (list_of_items ,item ):
    if item in list_of_items :
        list_of_items .remove (item )