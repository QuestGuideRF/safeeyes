import logging
from threading import Thread
from xmlrpc .server import SimpleXMLRPCServer
from xmlrpc .client import ServerProxy
class RPCServer :
    def __init__ (self ,port ,context ):
        self .__running =False
        logging .info ('Настройка сервера RPC на порту %d',port )
        self .__server =SimpleXMLRPCServer (("localhost",port ),logRequests =False ,allow_none =True )
        self .__server .register_function (context ['api']['show_settings'],'show_settings')
        self .__server .register_function (context ['api']['show_about'],'show_about')
        self .__server .register_function (context ['api']['enable_safeeyes'],'enable_safeeyes')
        self .__server .register_function (context ['api']['disable_safeeyes'],'disable_safeeyes')
        self .__server .register_function (context ['api']['take_break'],'take_break')
        self .__server .register_function (context ['api']['status'],'status')
        self .__server .register_function (context ['api']['quit'],'quit')
    def start (self ):
        if not self .__running :
            self .__running =True
            logging .info ('Запустите RPC-сервер')
            server_thread =Thread (target =self .__server .serve_forever )
            server_thread .start ()
    def stop (self ):
        if self .__running :
            logging .info ('Остановите сервер RPC')
            self .__running =False
            self .__server .shutdown ()
class RPCClient :
    def __init__ (self ,port ):
        self .port =port
        self .proxy =ServerProxy ('http://localhost:%d/'%self .port ,allow_none =True )
    def show_settings (self ):
        self .proxy .show_settings ()
    def show_about (self ):
        self .proxy .show_about ()
    def enable_safeeyes (self ):
        self .proxy .enable_safeeyes ()
    def disable_safeeyes (self ):
        self .proxy .disable_safeeyes (None )
    def take_break (self ):
        self .proxy .take_break ()
    def status (self ):
        return self .proxy .status ()
    def quit (self ):
        self .proxy .quit ()