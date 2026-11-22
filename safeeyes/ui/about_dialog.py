import os
from safeeyes import utility
ABOUT_DIALOG_GLADE =os .path .join (utility .BIN_DIRECTORY ,"glade/about_dialog.glade")
class AboutDialog :
    def __init__ (self ,version ):
        builder =utility .create_gtk_builder (ABOUT_DIALOG_GLADE )
        builder .connect_signals (self )
        self .window =builder .get_object ('window_about')
        builder .get_object ('lbl_decription').set_label (_ ("Safe Eyes protects your eyes from eye strain (asthenopia) by reminding you to take breaks while you're working long hours at the computer"))
        builder .get_object ('lbl_license').set_label (_ ('License')+':')
        builder .get_object ('lbl_app_name').set_label ('Безопасные глаза '+version )
    def show (self ):
        self .window .show_all ()
    def on_window_delete (self ,*args ):
        self .window .destroy ()
    def on_close_clicked (self ,*args ):
        self .window .destroy ()