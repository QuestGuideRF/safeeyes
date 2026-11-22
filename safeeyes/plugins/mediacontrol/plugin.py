import logging
import os
import dbus
import re
import gi
from safeeyes .model import TrayAction
gi .require_version ('Gtk','3.0')
from gi .repository import Gtk
tray_icon_path =None
def __active_players ():
    players =[]
    bus =dbus .SessionBus ()
    for service in bus .list_names ():
        if re .match ('org.mpris.MediaPlayer2.',service ):
            player =bus .get_object (service ,"/org/mpris/MediaPlayer2")
            interface =dbus .Interface (player ,'org.freedesktop.DBus.Properties')
            status =str (interface .Get ('org.mpris.MediaPlayer2.Player','PlaybackStatus')).lower ()
            if status =="playing":
                players .append (player )
    return players
def __pause_players (players ):
    for player in players :
        interface =dbus .Interface (player ,dbus_interface ='org.mpris.MediaPlayer2.Player')
        interface .Pause ()
def init (ctx ,safeeyes_config ,plugin_config ):
    global tray_icon_path
    tray_icon_path =os .path .join (plugin_config ['path'],"resource/pause.png")
def get_tray_action (break_obj ):
    players =__active_players ()
    if players :
        return TrayAction .build ("Пауза мультимедиа",
        tray_icon_path ,
        Gtk .STOCK_MEDIA_PAUSE ,
        lambda :__pause_players (players ))