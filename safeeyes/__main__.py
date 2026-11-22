import argparse
import gettext
import locale
import logging
import signal
import sys
from threading import Timer
import gi
import psutil
from safeeyes import utility
from safeeyes .model import Config
from safeeyes .safeeyes import SafeEyes
from safeeyes .safeeyes import SAFE_EYES_VERSION
from safeeyes .rpc import RPCClient
gi .require_version ('Gtk','3.0')
from gi .repository import Gtk
gettext .install ('safeeyes',utility .LOCALE_PATH )
def __running ():
    process_count =0
    for proc in psutil .process_iter ():
        if not proc .cmdline :
            continue
        try :
            if callable (proc .cmdline ):
                cmd_line =proc .cmdline ()
            else :
                cmd_line =proc .cmdline
            if ('python3'in cmd_line [0 ]or 'python'in cmd_line [0 ])and ('safeeyes'in cmd_line [1 ]or 'safeeyes'in cmd_line ):
                process_count +=1
                if process_count >1 :
                    return True
        except (IndexError ,psutil .NoSuchProcess ):
            pass
    return False
def __evaluate_arguments (args ,safe_eyes ):
    if args .about :
        utility .execute_main_thread (safe_eyes .show_about )
    elif args .disable :
        utility .execute_main_thread (safe_eyes .disable_safeeyes )
    elif args .enable :
        utility .execute_main_thread (safe_eyes .enable_safeeyes )
    elif args .settings :
        utility .execute_main_thread (safe_eyes .show_settings )
    elif args .take_break :
        utility .execute_main_thread (safe_eyes .take_break )
def main ():
    system_locale =gettext .translation ('safeeyes',localedir =utility .LOCALE_PATH ,languages =[utility .system_locale (),'en_US'],fallback =True )
    system_locale .install ()
    try :
        locale .bindtextdomain ('safeeyes',utility .LOCALE_PATH )
    except AttributeError :
        logging .warning ('установленный модуль gettext Python не поддерживает locale.bindtextdomain. locale.bindtextdomain требуется для файлов Glade.')
    parser =argparse .ArgumentParser (prog ='safeeyes',description =_ ('description'))
    group =parser .add_mutually_exclusive_group ()
    group .add_argument ('-a','--about',help =_ ('показать диалог о программе'),action ='store_true')
    group .add_argument ('-d','--disable',help =_ ('отключить текущий запущенный экземпляр Safeeyes'),action ='store_true')
    group .add_argument ('-e','--enable',help =_ ('включить работающий в данный момент экземпляр Safeeyes'),action ='store_true')
    group .add_argument ('-q','--quit',help =_ ('выйдите из работающего экземпляра Safeeyes и выйдите'),action ='store_true')
    group .add_argument ('-s','--settings',help =_ ('показать диалог настроек'),action ='store_true')
    group .add_argument ('-t','--take-break',help =_ ('Сделайте перерыв сейчас').lower (),action ='store_true')
    parser .add_argument ('--debug',help =_ ('запустить Safeeyes в режиме отладки'),action ='store_true')
    parser .add_argument ('--status',help =_ ('распечатать статус запущенного экземпляра Safeeyes и выйти'),action ='store_true')
    parser .add_argument ('--version',action ='version',version ='%(прог)с '+SAFE_EYES_VERSION )
    args =parser .parse_args ()
    utility .initialize_logging (args .debug )
    utility .initialize_platform ()
    config =Config ()
    if __running ():
        logging .info ("Safe Eyes уже работает")
        if not config .get ("use_rpc_server",True ):
            print (_ ('Safe Eyes работает без сервера RPC. Включите его, чтобы использовать аргументы командной строки.'))
            sys .exit (0 )
            return
        rpc_client =RPCClient (config .get ('rpc_port'))
        if args .about :
            rpc_client .show_about ()
        elif args .disable :
            rpc_client .disable_safeeyes ()
        elif args .enable :
            rpc_client .enable_safeeyes ()
        elif args .settings :
            rpc_client .show_settings ()
        elif args .take_break :
            rpc_client .take_break ()
        elif args .status :
            print (rpc_client .status ())
        elif args .quit :
            rpc_client .quit ()
        else :
            rpc_client .show_settings ()
        sys .exit (0 )
    else :
        if args .status :
            print (_ ('Safe Eyes не работает'))
            sys .exit (0 )
        elif not args .quit :
            logging .info ("Запуск Safe Eyes")
            safe_eyes =SafeEyes (system_locale ,config )
            safe_eyes .start ()
            Timer (1.0 ,lambda :__evaluate_arguments (args ,safe_eyes )).start ()
            Gtk .main ()
if __name__ =='__main__':
    signal .signal (signal .SIGINT ,signal .SIG_DFL )
    main ()