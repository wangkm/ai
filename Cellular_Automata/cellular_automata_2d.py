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
class CellStatus(Enum):
    dead = 0
    alive = 1


class Config():
    scale_x = 12
    scale_y = 12

    Color_border = wx.Colour(0, 0, 0)
    Color_background = wx.Colour(255, 255, 255) 
    Color_alive = wx.Colour(0, 0, 0)        # black
    Color_dead = wx.Colour(255, 255, 255)   # white
    side_size = 40

    interval = 0.2      # seconds
    
class DataStore():
    def __init__(self):
        self.reset()
    #----------------------------------------------------------------------
    def reset(self):
        self.gridInfos = [[ CellStatus.dead.value for col in range(Config.scale_y) ] for row in range(Config.scale_x) ]
        self.gridInfos[3][1] = CellStatus.alive.value
        self.gridInfos[1][2] = CellStatus.alive.value
        self.gridInfos[3][2] = CellStatus.alive.value
        self.gridInfos[2][3] = CellStatus.alive.value
        self.gridInfos[3][3] = CellStatus.alive.value


# global variable
dataStore = DataStore()

# x, y is index of dim 1 and dim 2, not position!
def get_next_status(x, y, gridInfos):
    # get 8 neighbour info, [alive, dead]
    pre_y = y - 1 if (y > 0) else Config.scale_y - 1
    pre_x = x - 1 if (x > 0) else Config.scale_x - 1
    next_y = y + 1 if (y < Config.scale_y - 1) else 0
    next_x = x + 1 if (x < Config.scale_x - 1) else 0

    alive_count = 0
    dead_count = 0

    cell_status = gridInfos[x][pre_y]
    if(cell_status == CellStatus.alive.value):
        alive_count += 1
    else:
        dead_count += 1
    cell_status = gridInfos[pre_x][pre_y]
    if(cell_status == CellStatus.alive.value):
        alive_count += 1
    else:
        dead_count += 1
    cell_status = gridInfos[pre_x][y]
    if(cell_status == CellStatus.alive.value):
        alive_count += 1
    else:
        dead_count += 1
    cell_status = gridInfos[pre_x][next_y]
    if(cell_status == CellStatus.alive.value):
        alive_count += 1
    else:
        dead_count += 1
    cell_status = gridInfos[x][next_y]
    if(cell_status == CellStatus.alive.value):
        alive_count += 1
    else:
        dead_count += 1
    cell_status = gridInfos[next_x][next_y]
    if(cell_status == CellStatus.alive.value):
        alive_count += 1
    else:
        dead_count += 1
    cell_status = gridInfos[next_x][y]
    if(cell_status == CellStatus.alive.value):
        alive_count += 1
    else:
        dead_count += 1
    cell_status = gridInfos[next_x][pre_y]
    if(cell_status == CellStatus.alive.value):
        alive_count += 1
    else:
        dead_count += 1
    neighbour_info = [alive_count, dead_count]

    if(gridInfos[x][y] == CellStatus.dead.value):
        if(neighbour_info[0] == 3):
            return CellStatus.alive.value
    else:
        if(neighbour_info[0] < 2 or neighbour_info[0] > 3):
            return CellStatus.dead.value
    return gridInfos[x][y]

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
        for i in range(100):
            if self._want_abort:
                wx.PostEvent(self._notify_window, ResultEvent("Aborted"))
                return

            print("step = %d" % i)
            print(dataStore.gridInfos)
            new_gridInfos = [[ 0 for col in range(Config.scale_y) ] for row in range(Config.scale_x) ]
            for x in range(Config.scale_x):
                for y in range(Config.scale_y):
                    new_gridInfos[x][y] = get_next_status(x, y, dataStore.gridInfos)

            dataStore.gridInfos = new_gridInfos

            wx.PostEvent(self._notify_window, ResultEvent(i))
            time.sleep(Config.interval)

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
        self.SetSize((Config.scale_x + 2) * Config.side_size + 12 , (Config.scale_y + 2) * Config.side_size + 80)
        #self.Centre()

     #----------------------------------------------------------------------       
    def OnPaint(self, e):
        dc = wx.PaintDC(self)

        offset_x = Config.side_size
        offset_y = Config.side_size

        global dataStore

        # draw Matrix Background
        dc.SetPen(wx.Pen(Config.Color_border, 1, wx.SOLID))
        dc.SetBrush(wx.Brush(Config.Color_background, wx.SOLID)) 
        dc.DrawRectangle(offset_x, offset_y, Config.scale_x * Config.side_size, Config.scale_y * Config.side_size)

        # Vertical lines
        for i in range(1, Config.scale_x):
            dc.DrawLine(offset_x + i * Config.side_size, offset_y, 
                        offset_x + i * Config.side_size, offset_y + Config.scale_y * Config.side_size)
        
        # Horizontal lines
        for i in range(1, Config.scale_y):
            dc.DrawLine(offset_x, offset_y + i * Config.side_size, 
                        offset_x + Config.scale_x * Config.side_size, offset_y + i * Config.side_size)

        # Pain Grid
        dc.SetPen(wx.Pen(Config.Color_border, 1, wx.TRANSPARENT))
        for i in range(Config.scale_x):
            for j in range(Config.scale_y):
                if(dataStore.gridInfos[i][j] == CellStatus.alive.value):
                    dc.SetBrush(wx.Brush(Config.Color_alive, wx.SOLID))
                else:
                    dc.SetBrush(wx.Brush(Config.Color_dead, wx.SOLID))
               
                dc.DrawRectangle(offset_x + i * Config.side_size + 1, offset_y + j * Config.side_size + 1, 
                         Config.side_size - 1, Config.side_size - 1)
        
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

def main():
    app = wx.App()
    mainWnd = MyFrame(None)
    mainWnd.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()