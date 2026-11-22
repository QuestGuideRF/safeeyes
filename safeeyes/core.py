import datetime
import logging
import threading
import time
from safeeyes import utility
from safeeyes .model import Break
from safeeyes .model import BreakType
from safeeyes .model import BreakQueue
from safeeyes .model import EventHook
from safeeyes .model import State
class SafeEyesCore :
    def __init__ (self ,context ):
        self .break_queue =None
        self .postpone_duration =0
        self .default_postpone_duration =0
        self .pre_break_warning_time =0
        self .running =False
        self .scheduled_next_break_timestamp =-1
        self .scheduled_next_break_time =None
        self .paused_time =-1
        self .on_pre_break =EventHook ()
        self .on_start_break =EventHook ()
        self .start_break =EventHook ()
        self .on_count_down =EventHook ()
        self .on_stop_break =EventHook ()
        self .on_update_next_break =EventHook ()
        self .waiting_condition =threading .Condition ()
        self .lock =threading .Lock ()
        self .context =context
        self .context ['skipped']=False
        self .context ['postponed']=False
        self .context ['state']=State .WAITING
    def initialize (self ,config ):
        logging .info ("Инициализировать ядро")
        self .pre_break_warning_time =config .get ('pre_break_warning_time')
        self .break_queue =BreakQueue (config ,self .context )
        self .default_postpone_duration =config .get ('postpone_duration')*60
        self .postpone_duration =self .default_postpone_duration
    def start (self ,next_break_time =-1 ,reset_breaks =False ):
        if self .break_queue .is_empty ():
            return
        with self .lock :
            if not self .running :
                logging .info ("Запустить ядро ​​Safe Eyes")
                if reset_breaks :
                    logging .info ("Сбросьте перерывы, чтобы начать с самого начала")
                    self .break_queue .reset ()
                self .running =True
                self .scheduled_next_break_timestamp =int (next_break_time )
                utility .start_thread (self .__scheduler_job )
    def stop (self ,is_resting =False ):
        with self .lock :
            if not self .running :
                return
            logging .info ("Ядро Stop Safe Eyes")
            self .paused_time =datetime .datetime .now ().timestamp ()
            self .waiting_condition .acquire ()
            self .running =False
            if self .context ['state']!=State .QUIT :
                self .context ['state']=State .RESTING if (is_resting )else State .STOPPED
            self .waiting_condition .notify_all ()
            self .waiting_condition .release ()
    def skip (self ):
        self .context ['skipped']=True
    def postpone (self ,duration =-1 ):
        if duration >0 :
            self .postpone_duration =duration
        else :
            self .postpone_duration =self .default_postpone_duration
        logging .debug ("Отложить перерыв на %d секунд.",self .postpone_duration )
        self .context ['postponed']=True
    def get_break_time (self ,break_type =None ):
        break_obj =self .break_queue .get_break (break_type )
        if not break_obj :
            return False
        time =self .scheduled_next_break_time +datetime .timedelta (minutes =break_obj .time -self .break_queue .get_break ().time )
        return time
    def take_break (self ,break_type =None ):
        if self .break_queue .is_empty ():
            return
        if not self .context ['state']==State .WAITING :
            return
        utility .start_thread (self .__take_break ,break_type =break_type )
    def has_breaks (self ,break_type =None ):
        return not self .break_queue .is_empty (break_type )
    def __take_break (self ,break_type =None ):
        logging .info ('Сделайте перерыв по внешнему запросу')
        with self .lock :
            if not self .running :
                return
            logging .info ("Остановить планировщик")
            self .waiting_condition .acquire ()
            self .running =False
            self .waiting_condition .notify_all ()
            self .waiting_condition .release ()
            time .sleep (1 )
            self .running =True
        if break_type is not None and self .break_queue .get_break ().type !=break_type :
            self .break_queue .next (break_type )
        utility .execute_main_thread (self .__fire_start_break )
    def __scheduler_job (self ):
        if not self .running :
            return
        current_time =datetime .datetime .now ()
        current_timestamp =current_time .timestamp ()
        if self .context ['state']==State .RESTING and self .paused_time >-1 :
            paused_duration =int (current_timestamp -self .paused_time )
            self .paused_time =-1
            if paused_duration >self .break_queue .get_break (BreakType .LONG_BREAK ).duration :
                logging .info ('Пропустить следующий длинный перерыв, так как пауза %d превышает продолжительность перерыва.',paused_duration )
                self .break_queue .reset ()
        if self .context ['postponed']:
            logging .info ('Готовьтесь к отложенному перерыву')
            time_to_wait =self .postpone_duration
            self .context ['postponed']=False
        elif current_timestamp <self .scheduled_next_break_timestamp :
            time_to_wait =round (self .scheduled_next_break_timestamp -current_timestamp )
            self .scheduled_next_break_timestamp =-1
        else :
            time_to_wait =self .break_queue .get_break ().time *60
        self .scheduled_next_break_time =current_time +datetime .timedelta (seconds =time_to_wait )
        self .context ['state']=State .WAITING
        utility .execute_main_thread (self .__fire_on_update_next_break ,self .scheduled_next_break_time )
        logging .info ("Ожидание %d минут до следующего перерыва",(time_to_wait /60 ))
        self .__wait_for (time_to_wait )
        logging .info ("Предперерывное ожидание закончилось")
        if not self .running :
            return
        utility .execute_main_thread (self .__fire_pre_break )
    def __fire_on_update_next_break (self ,next_break_time ):
        self .on_update_next_break .fire (self .break_queue .get_break (),next_break_time )
    def __fire_pre_break (self ):
        self .context ['state']=State .PRE_BREAK
        if not self .on_pre_break .fire (self .break_queue .get_break ()):
            self .__start_next_break ()
            return
        utility .start_thread (self .__wait_until_prepare )
    def __wait_until_prepare (self ):
        logging .info ("Подождите %d секунд перед перерывом.",self .pre_break_warning_time )
        self .__wait_for (self .pre_break_warning_time )
        if not self .running :
            return
        utility .execute_main_thread (self .__fire_start_break )
    def __postpone_break (self ):
        self .__wait_for (self .postpone_duration )
        utility .execute_main_thread (self .__fire_start_break )
    def __fire_start_break (self ):
        break_obj =self .break_queue .get_break ()
        if not self .on_start_break .fire (break_obj ):
            self .__start_next_break ()
            return
        if self .context ['postponed']:
            self .context ['postponed']=False
            self .scheduled_next_break_time =self .scheduled_next_break_time +datetime .timedelta (seconds =self .postpone_duration )
            self .__fire_on_update_next_break (self .scheduled_next_break_time )
            utility .start_thread (self .__postpone_break )
        else :
            self .start_break .fire (break_obj )
            utility .start_thread (self .__start_break )
    def __start_break (self ):
        self .context ['state']=State .BREAK
        break_obj =self .break_queue .get_break ()
        countdown =break_obj .duration
        total_break_time =countdown
        while countdown and self .running and not self .context ['skipped']and not self .context ['postponed']:
            seconds =total_break_time -countdown
            self .on_count_down .fire (countdown ,seconds )
            time .sleep (1 )
            countdown -=1
        utility .execute_main_thread (self .__fire_stop_break )
    def __fire_stop_break (self ):
        if not self .context ['skipped']and not self .context ['postponed']:
            logging .info ("Перерыв прекращается автоматически")
            self .on_stop_break .fire ()
        self .context ['skipped']=False
        self .__start_next_break ()
    def __wait_for (self ,duration ):
        self .waiting_condition .acquire ()
        self .waiting_condition .wait (duration )
        self .waiting_condition .release ()
    def __start_next_break (self ):
        if not self .context ['postponed']:
            self .break_queue .next ()
        if self .running :
            utility .start_thread (self .__scheduler_job )