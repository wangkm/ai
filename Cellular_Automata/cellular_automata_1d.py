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

class Config():
    rule_str = '00011110'
    scale = 200
    evolution_max = 200
    Color_one = wx.Colour(0, 0, 255)   # black
    Color_zero = wx.Colour(255, 255, 255)   # white
    grid_size = 2

class DataStore():
    def __init__(self):
        self.evolution_history = list()
        data_list = list()
        for i in range(Config.scale):
            data_list.append(random.randint(0, 1))
        self.evolution_history.append(data_list)

# global variable
dataStore = DataStore()

def convert_dec_to_binstr(num):
    binstr = bin(int(str(num), 10))
    return binstr[2:]

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


class MyFrame(wx.Frame):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.InitUI()

    #----------------------------------------------------------------------
    def InitUI(self):
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetTitle("Cellular Automata")

        # set size and position
        global dataStore
        self.SetSize(Config.scale * Config.grid_size + 16 , Config.evolution_max * Config.grid_size + 41)
        #self.Centre()

    #----------------------------------------------------------------------       
    def OnPaint(self, e):
        dc = wx.PaintDC(self)
        global dataStore
        dc.SetPen(wx.Pen(Config.Color_one, 1, wx.TRANSPARENT))
        # draw points based on evolution_history
        y = 0       
        for data_list in dataStore.evolution_history:
            #print(data_list)
            x = 0
            for data in data_list:
                if(data == 1):
                    dc.SetBrush(wx.Brush(Config.Color_one, wx.SOLID))
                    dc.DrawRectangle(x, y, Config.grid_size, Config.grid_size)
                elif(data == 0):
                    dc.SetBrush(wx.Brush(Config.Color_zero, wx.SOLID))
                    dc.DrawRectangle(x, y, Config.grid_size, Config.grid_size)
                else:
                    raise("Invalid data: %d" %data)
                x += Config.grid_size
            y += Config.grid_size
        #self.saveDCToFile("222")    

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

    global dataStore
    evolution_count = 0
    while(evolution_count < Config.evolution_max):
        current_data_list = dataStore.evolution_history[-1]     # the last element of evolution_history
        new_data_list = list()
        for i in range(Config.scale):
            new_data_list.append(get_evolution_value(i, current_data_list))
        dataStore.evolution_history.append(new_data_list)
        evolution_count += 1

    app = wx.App()
    mainWnd = MyFrame(None)
    mainWnd.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()