#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import wx
import time
from threading import *
import numpy as np
from enum import Enum, unique
import random
import itertools

@unique
class Thread_Result(Enum):
    aborted = 0
    finished = 1

def convert_dec_to_binstr(num, length):
    binstr = bin(int(str(num), 10))
    binstr = binstr[2:]
    while len(binstr) < length:
        binstr = '0' + binstr
    return binstr


class Config():
    #rule_str = '01101110'       # rule 110
    #rule_str = '00011110'       # rule 30
    #rule_str = '10100101'       # rule 165
    #rule_str = '01001101'       # rule 77
    #rule_str = '01101001'       # rule 77
    rule_str = None
    scale = 300
    evolution_max = 300
    #Color_one = wx.Colour(0, 0, 0)   # black
    #Color_zero = wx.Colour(255, 255, 255)   # white
    grid_size = 2
    interval = 2

class DataStore():
    def __init__(self):
        self.reset()

    def reset(self):
        self.evolution_history = list()
        data_list = list()
        for i in range(Config.scale):
            #data_list.append(i % 2)
            #data_list.append(0)
            data_list.append(random.randint(0, 1))
        #data_list[-1] = 1
        self.evolution_history.append(data_list)

# global variable
dataStore = DataStore()

# x, y is index of dim 1 and dim 2, not position!
def get_evolution_value(index, data_list) -> int:
    pre_index = index - 1 if (index > 0) else Config.scale - 1
    next_index = index + 1 if (index < Config.scale - 1) else 0

    condition = str(data_list[pre_index]) + str(data_list[index]) + str(data_list[next_index])
    return evolution_rule(condition)

def evolution_rule(condition: str) -> int:
    if(condition == '000'):
        return int(Config.rule_str[7])
    if(condition == '001'):
        return int(Config.rule_str[6])
    if(condition == '010'):
        return int(Config.rule_str[5])
    if(condition == '011'):
        return int(Config.rule_str[4])
    if(condition == '100'):
        return int(Config.rule_str[3])
    if(condition == '101'):
        return int(Config.rule_str[2])
    if(condition == '110'):
        return int(Config.rule_str[1])
    if(condition == '111'):
        return int(Config.rule_str[0])
    else:
        raise Exception('Invalid condition: ' + condition)

# Define notification event for thread completion
EVT_RESULT_ID = wx.NewIdRef()

class ResultEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

# Thread class that executes processing
class WorkerThread(Thread):
    def __init__(self, notify_window):
        Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = False
        self._is_train = False

    def run(self):
        global dataStore
        for i in range(255):
            print("working with i = %d" %i)
            dataStore.reset()
            Config.rule_str = convert_dec_to_binstr(i, 8)
            evolution_count = 0
            while(evolution_count < Config.evolution_max):
                current_data_list = dataStore.evolution_history[-1]     # the last element of evolution_history
                new_data_list = list()
                for i in range(Config.scale):
                    new_data_list.append(get_evolution_value(i, current_data_list))
                dataStore.evolution_history.append(new_data_list)
                evolution_count += 1
            wx.PostEvent(self._notify_window, ResultEvent(i))
            time.sleep(Config.interval)

            if self._want_abort:
                wx.PostEvent(self._notify_window, ResultEvent("Aborted"))
                return

    def abort(self):
        self._want_abort = True

class MyFrame(wx.Frame):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.InitUI()
        self.Connect(-1, -1, EVT_RESULT_ID, self.OnResult) # Set up event handler for any worker thread results
        self.worker = None # And indicate we don't have a worker thread yet

    #----------------------------------------------------------------------
    def InitUI(self):
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetTitle("Cellular Automata")
        
        # add menubar
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()

        self.startMenuItem = fileMenu.Append(wx.NewIdRef(), "Start", "Start evolution")
        self.Bind(wx.EVT_MENU, self.onStart, self.startMenuItem)

        self.stopMenuItem = fileMenu.Append(wx.NewIdRef(), "Stop", "Stop evolution")
        self.Bind(wx.EVT_MENU, self.onStop, self.stopMenuItem)
        self.stopMenuItem.Enable(False)

        self.resetMenuItem = fileMenu.Append(wx.NewIdRef(), "Reset", "Reset condition")
        self.Bind(wx.EVT_MENU, self.onReset, self.resetMenuItem)

        fileMenu.AppendSeparator()

        self.exitMenuItem = fileMenu.Append(wx.NewIdRef(), "Exit", "Exit application")
        self.Bind(wx.EVT_MENU, self.onExit, self.exitMenuItem)   

        menuBar.Append(fileMenu, "&File")
        self.SetMenuBar(menuBar)

        # add statusbar
        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText('ok')

        # set size and position
        global dataStore
        self.SetSize(Config.scale * Config.grid_size + 16 , Config.evolution_max * Config.grid_size + 100)
        self.Centre()

    #----------------------------------------------------------------------       
    def OnPaint(self, e):
        if Config.rule_str is None:
            return

        global dataStore
        #dc = wx.BufferedPaintDC (self)
        dc = wx.PaintDC (self)
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1, wx.TRANSPARENT))
        dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0), wx.SOLID))
        # draw points based on evolution_history
        y = 0       
        for data_list in dataStore.evolution_history:
            x = 0
            for data in data_list:
                if(data == 1):
                    dc.DrawRectangle(x, y, Config.grid_size, Config.grid_size)  # only draw data = 1
                x += Config.grid_size
            y += Config.grid_size
        self.saveDCToFile(Config.rule_str)    

     #----------------------------------------------------------------------   
    def onExit(self, event):
        if self.worker:
            self.worker.abort()
        self.Close()

    #----------------------------------------------------------------------
    def onStart(self, event):
        if not self.worker:
            self.worker = WorkerThread(self)
            self.worker._is_train = False
            self.worker.start()
            self.startMenuItem.Enable(False)
            self.stopMenuItem.Enable(True)
        else:
            raise Exception("worker is running!")

    #----------------------------------------------------------------------
    def onStop(self, event):
        if self.worker:
            self.worker.abort()
            self.worker = None
        else:
            raise Exception("worker is not running!")
        self.startMenuItem.Enable(True)
        self.stopMenuItem.Enable(False)
        self.statusbar.SetStatusText('Stopped')
    
     #----------------------------------------------------------------------
    def onReset(self, event):
        self.reset()

    #----------------------------------------------------------------------
    def reset(self):
        if self.worker:
            self.worker.abort()
            self.worker = None
            self.startMenuItem.Enable(True)
            self.stopMenuItem.Enable(False)        
        global dataStore
        dataStore.reset()
        self.Refresh()
    #----------------------------------------------------------------------
    def OnResult(self, event):
        self.Refresh()
        self.statusbar.SetStatusText('Evolution steps: %s' % event.data)
        if(event.data == "Stopped"):
            self.worker = None
            self.startMenuItem.Enable(True)
            self.stopMenuItem.Enable(False)           

    #----------------------------------------------------------------------
    def saveDCToFile(self, name):
        context = wx.ClientDC( self )
        memory = wx.MemoryDC( )
        x, y = self.ClientSize
        bitmap = wx.Bitmap( x, y, -1 )
        memory.SelectObject( bitmap )
        memory.Blit( 0, 0, x, y, context, 0, 0)
        memory.SelectObject( wx.NullBitmap)
        bitmap.SaveFile(name + '.jpg', wx.BITMAP_TYPE_JPEG )    


def main():
    app = wx.App()
    mainWnd = MyFrame(None)
    mainWnd.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
