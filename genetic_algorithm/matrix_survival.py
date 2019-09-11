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
class RobotName(Enum):
    A = 0
    B = 1

@unique
class GridStatus(Enum):
    wall = 0
    initial = 1
    pained_by_A = 2
    pained_by_B = 3

@unique
class Action(Enum):
    forward = 0
    turn_left = 1
    turn_right = 2

@unique
class Direction(Enum):
    north = 0
    south = 1
    west = 2
    east = 3

class Configuration():
    init_genelib_size = 2000
    evolution_limit = 100
    variability_ratio = 0.005
    gene_length = pow(4, 5)     # four grids and self direction
    interval = 0.2              # second
    scale_x = 12
    scale_y = 12
    max_steps = scale_x * scale_y * 2
    #genelib_size = 200         # must can be divided by 4

    Color_border = wx.Colour(0, 0, 0)
    Color_background = wx.Colour(255, 255, 255)
    Color_A = wx.Colour(100, 0, 0)
    Color_B = wx.Colour(0, 0, 100)
    side_size = 40
    
class DataStore():
    def __init__(self):
        self.init_conditions()
        self.reset()
    #----------------------------------------------------------------------
    def reset(self):
        self.gridInfos = np.full((Configuration.scale_x, Configuration.scale_y), GridStatus.initial)
        self.position_A = [0, 0]
        self.direction_A = Direction.south
        self.gridInfos[self.position_A[0]][self.position_A[1]] = GridStatus.pained_by_A
        self.position_B = [Configuration.scale_x - 1, Configuration.scale_y - 1]
        self.direction_B = Direction.north
        self.gridInfos[self.position_B[0]][self.position_B[1]] = GridStatus.pained_by_B
    #----------------------------------------------------------------------
    # generate report
    def get_result(self):
        score_A = 0
        score_B = 0
        for i in range(Configuration.scale_x):
            for j in range(Configuration.scale_y):
                if(self.gridInfos[i][j] == GridStatus.pained_by_A):
                    score_A += 1
                elif(self.gridInfos[i][j] == GridStatus.pained_by_B):
                    score_B += 1
        
        return score_A, score_B 
    #----------------------------------------------------------------------
    # init conditions
    def init_conditions(self):
        print("start initial conditions..", end = '')
        self.conditions = dict()
        index = 0
        for p0 in range(4):
            for p1 in range(4):
                for p2 in range(4):
                    for p3 in range(4):
                        for p4 in range(4):
                            key = str(p0) + str(p1) + str(p2) + str(p3) + str(p4)
                            self.conditions[key] = index
                            index += 1                           
        print("done")

# global variable
dataStore = DataStore()


class Robot():
    def __init__(self, name: RobotName):
        self._name = name

    def do_action(self, strategy, data = None):
        global dataStore
        direction = dataStore.direction_A if self._name == RobotName.A else dataStore.direction_B
        position = dataStore.position_A if self._name == RobotName.A else dataStore.position_B
        grid_status = GridStatus.pained_by_A if self._name == RobotName.A else GridStatus.pained_by_B

        action = strategy(self._name, data)
        if(action == Action.forward):   
            if(direction == Direction.north and position[1] != 0):
                position[1] -= 1
            elif direction == Direction.south and position[1] != Configuration.scale_y - 1:
                position[1] += 1
            elif direction == Direction.west and position[0] != 0:
                position[0] -= 1
            elif direction == Direction.east and position[0] != Configuration.scale_x - 1:
                position[0] += 1
            else:       # 如果撞墙，随机调整一下方向
                direction = Direction(random.randint(0, 3))
        elif(action == Action.turn_left):
            if(direction == Direction.north):
                direction = Direction.west
            elif(direction == Direction.west):
                direction = Direction.south
            elif(direction == Direction.south):
                direction = Direction.east
            elif(direction == Direction.east):
                direction = Direction.north
        elif(action == Action.turn_right):
            if(direction == Direction.north):
                direction =  Direction.east
            elif(direction == Direction.west):
                direction =  Direction.north
            elif(direction == Direction.south):
                direction =  Direction.west
            elif(direction == Direction.east):
                direction =  Direction.south
        else:
            raise Exception("Invalid action: %s" % action)

        if self._name == RobotName.A:
            dataStore.direction_A = direction
        elif self._name == RobotName.B:
            dataStore.direction_B = direction
        dataStore.gridInfos[position[0]][position[1]] = grid_status

class StrategyLib():
    @staticmethod
    def strategy_random(robot_name: RobotName, data):
        if data is None:
            return Action(random.randint(0, 2))
        if data == "forward_first":
            global dataStore
            direction = dataStore.direction_A if robot_name == RobotName.A else dataStore.direction_B
            position = dataStore.position_A if robot_name == RobotName.A else dataStore.position_B
            grid_status = GridStatus.pained_by_A if robot_name == RobotName.A else GridStatus.pained_by_B

            # forward if possible
            if((direction == Direction.north and position[1] != 0 and dataStore.gridInfos[position[0]][position[1] - 1] != grid_status)
                    or (direction == Direction.south and position[1] != Configuration.scale_y - 1 and dataStore.gridInfos[position[0]][position[1] + 1] != grid_status)
                    or (direction == Direction.west and position[0] != 0 and dataStore.gridInfos[position[0] - 1][position[1]] != grid_status)
                    or (direction == Direction.east and position[0] != Configuration.scale_x - 1 and dataStore.gridInfos[position[0] + 1][position[1]] != grid_status)):
                return Action.forward
            else:
                return Action(random.randint(0, 2))

    # data is gene. gene is a long string of 0, 1, or 2. length = pow(4, 9) 
    @staticmethod
    def strategy_gene(robot_name: RobotName, gene) -> Action:
        global dataStore
        x = dataStore.position_A[0] if robot_name == RobotName.A else dataStore.position_B[0]
        y = dataStore.position_A[1] if robot_name == RobotName.A else dataStore.position_B[1]
        direction = dataStore.direction_A if robot_name == RobotName.A else dataStore.direction_B


        north = dataStore.gridInfos[x][y - 1].value if(y > 0) else GridStatus.wall.value
        #northwest = dataStore.gridInfos[x - 1][y - 1].value if (x > 0 and y > 0) else GridStatus.wall.value
        west = dataStore.gridInfos[x - 1][y].value if(x > 0) else GridStatus.wall.value
        #southwest = dataStore.gridInfos[x - 1][y + 1].value if (x > 0 and y < Configuration.scale_y - 1) else GridStatus.wall.value
        south = dataStore.gridInfos[x][y + 1].value if(y < Configuration.scale_y - 1) else GridStatus.wall.value
        #southeast = dataStore.gridInfos[x + 1][y + 1].value if (x < Configuration.scale_x - 1 and y < Configuration.scale_y - 1) else GridStatus.wall.value
        east = dataStore.gridInfos[x + 1][y].value if(x < Configuration.scale_x - 1) else GridStatus.wall.value
        #northeast = dataStore.gridInfos[x + 1][y - 1].value if (x < Configuration.scale_x - 1 and y > 0) else GridStatus.wall.value
        #condition = str(north) + str(northwest) + str(west) + str(southwest) + str(south) + str(southeast) + str(east) + str(northeast) + str(direction)
        condition = str(north) + str(west) + str(south) + str(east) + str(direction.value)

        index = dataStore.conditions[condition]
        action = Action(int(gene[index]))
        return action

Robot_A = Robot(RobotName.A)
Robot_B = Robot(RobotName.B)
        
# create gene libs
def init_gene_libs():
    global dataStore
    print("start initial init_genelibs..", end = '')
    gene_libs = list()
    for i in range(Configuration.init_genelib_size):
        gene = ""
        for j in range(Configuration.gene_length):
            action = Action(random.randint(0, 2))
            
            # turn_left后不能turn_right
            if(j > 0):
                pre_action = Action(int(gene[j - 1]))
                while (pre_action == Action.turn_left and action == Action.turn_right):
                    action = Action(random.randint(0, 2))
            # # 不能连续4个转向，如果发生，最后一个改成forward
            # if(j > 4):
            #     if((gene[j - 1] == gene[j - 2] == gene[j - 3]) and gene[j - 1] != Action.forward.value):
            #         action = Action.forward
            
            # # 如果撞墙，则逆时针转一下
            # if(action == Action.forward):
            #     condition = index_condition_dict[j]
            #     if(condition[4] == str(Direction.north.value) and condition[0] == str(GridStatus.wall)):
            #         action = Action.turn_left if(condition[1] != str(GridStatus.wall)) else Action.turn_right
            #     elif(condition[4] == str(Direction.west.value) and condition[1] == str(GridStatus.wall)):
            #         action = Action.turn_left if(condition[2] != str(GridStatus.wall)) else Action.turn_right
            #     elif(condition[4] == str(Direction.south.value) and condition[2] == str(GridStatus.wall)):
            #         action = Action.turn_left if(condition[3] != str(GridStatus.wall)) else Action.turn_right
            #     elif(condition[4] == str(Direction.west.value) and condition[3] == str(GridStatus.wall)):
            #         action = Action.turn_left if(condition[0] != str(GridStatus.wall)) else Action.turn_right

            gene += str(action.value)
        gene_libs.append([gene, 0])
    print('done')
    return gene_libs

def sortSecond(val): 
    return val[1] 

def replace_char(s: str, idx: int, ch: str) -> str:
    s1 = s[:idx] + ch + s[idx + 1:]
    return s1

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
        if(self._is_train):
            gene_libs = init_gene_libs()
            variability_count = int(Configuration.gene_length * Configuration.variability_ratio)

            evolution_count = 0
            while evolution_count < Configuration.evolution_limit:
                
                score_B_best = 0
                for gene_info in gene_libs:
                    try_times = 3
                    score_B_sum = 0                  
                    # 每个策略跑若干次
                    for try_time in range(try_times):
                        dataStore.reset()
                        for i in range(Configuration.max_steps):
                            #Robot_A.do_action(StrategyLib.strategy_random)
                            Robot_A.do_action(StrategyLib.strategy_random, "forward_first")
                            Robot_B.do_action(StrategyLib.strategy_gene, gene_info[0])
                        score_A, score_B = dataStore.get_result()
                        score_B_sum += score_B
                        
                    score_B_avarage = int(score_B_sum / try_times)
                    if(score_B_avarage > score_B_best):
                        score_B_best = score_B_avarage

                    data = 'evolution_count = %d, score_B_avarage = %d, score_B_best = %d' % (evolution_count, score_B_avarage, score_B_best)
                    print(data)
                    #score_A, score_B = dataStore.get_result()
                    #data = 'evolution_count = %d, score_A = %d, score_B = %d' % (evolution_count, score_A, score_B)
                    
                    gene_info[1] = score_B_avarage
                    

                # sort gene libs
                gene_libs.sort(key = sortSecond, reverse=True)
                new_gene_libs = gene_libs[:100]

                print("evolution_count = %d, best_record = %d" % (evolution_count, new_gene_libs[0][1]))

                for i in range(50):
                    gene_f = new_gene_libs[i * 2][0]
                    gene_m = new_gene_libs[i * 2 + 1][0]
                    new_gene_1 = gene_f[0 : int(Configuration.gene_length / 2) + 1] + gene_m[int(Configuration.gene_length / 2) + 1 : Configuration.gene_length]
                    new_gene_2 = gene_m[0 : int(Configuration.gene_length / 2) + 1] + gene_f[int(Configuration.gene_length / 2) + 1 : Configuration.gene_length]
                    # for v in range(variability_count):
                    #     pos = random.randint(0, Configuration.gene_length - 1)
                    #     new_gene_1 = replace_char(new_gene_1, pos, str(random.randint(0, 2)))
                    #     pos = random.randint(0, Configuration.gene_length - 1)
                    #     new_gene_2 = replace_char(new_gene_2, pos, str(random.randint(0, 2)))

                    new_gene_libs.append([new_gene_1, 0])
                    new_gene_libs.append([new_gene_2, 0])
                gene_libs = new_gene_libs

                evolution_count += 1

            #print best 10 strategries
            gene_libs.sort(key = sortSecond, reverse=True)
            for i in range(10):
                print("%s, %d" %(gene_libs[i][0], gene_libs[i][1]))

        else:
            for i in range(Configuration.max_steps):
                if self._want_abort:
                    wx.PostEvent(self._notify_window, ResultEvent("Aborted"))
                    return
                
                gene = '1021000121102200020121201021001000110120022002011110101110201020021001002001020201110001010101022020210002010000200220202000210100111110210101011111201020020101111101022110201110022121010001011201111121002110101000102200010102002100100211100002222020201111101002111110221011101002101002222202202101000110200220022201000001021111010221011001000211110222120212100202000211021102020021011000021221010111102201111112101211112211102220022011020121001001102011020120210001100201120201101020210220020000120211101021102001102000110000010010210202120211001010020012211001100111110111000222002011010010121110020020012001000221111010200020000221111111002200110010102002220201021111210100111120022100020102010021001102221020202000000000100202201110110012110121100001002110220120022022200200122121011002220110011011111201110021200222111002001200201110120010102102020110002220010102120220202200211021021002211112202100202021011110111020110011100100110011000111202110100001010120211001101200201000221002002222010221020020022110110121002022'
                #Robot_A.do_action(StrategyLib.strategy_random)
                #Robot_A.do_action(StrategyLib.strategy_random, "forward_first")
                Robot_B.do_action(StrategyLib.strategy_gene, gene)

                wx.PostEvent(self._notify_window, ResultEvent(i))
                time.sleep(Configuration.interval)

            score_A, score_B = dataStore.get_result()
            data = 'score_A = %d, score_B = %d' % (score_A, score_B)
            wx.PostEvent(self._notify_window, ResultEvent("Finished: %s" % data))

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
        self.SetTitle("Matrix Survival")
        
        # add menubar
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()

        self.startMenuItem = fileMenu.Append(wx.NewIdRef(), "Start", "Start evolution")
        self.Bind(wx.EVT_MENU, self.onStart, self.startMenuItem)

        self.trainMenuItem = fileMenu.Append(wx.NewIdRef(), "Train", "Train robot")
        self.Bind(wx.EVT_MENU, self.onTrain, self.trainMenuItem)

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
        self.SetSize((Configuration.scale_x + 2) * Configuration.side_size + 12 , (Configuration.scale_y + 2) * Configuration.side_size + 80)
        #self.Centre()

    # calculate angle and postion adjust from robot direction
    def getAngleAndAdjust(self, direction):
        if(direction == Direction.north):
            angle = 0
            adjust_x = 8
            adjust_y = 5
        elif(direction == Direction.west):
            angle = 90
            adjust_x = 8
            adjust_y = 33
        elif(direction == Direction.south):
            angle = 180
            adjust_x = 33
            adjust_y = 33
        elif(direction == Direction.east):
            angle = 270
            adjust_x = 33
            adjust_y = 8
        return angle, adjust_x, adjust_y
     #----------------------------------------------------------------------       
    def OnPaint(self, e):
        dc = wx.PaintDC(self)

        offset_x = Configuration.side_size
        offset_y = Configuration.side_size

        global dataStore

        # draw Matrix Background
        dc.SetPen(wx.Pen(Configuration.Color_border, 1, wx.SOLID))
        dc.SetBrush(wx.Brush(Configuration.Color_background, wx.SOLID)) 
        dc.DrawRectangle(offset_x, offset_y, Configuration.scale_x * Configuration.side_size, Configuration.scale_y * Configuration.side_size)

        # Vertical lines
        for i in range(1, Configuration.scale_x):
            dc.DrawLine(offset_x + i * Configuration.side_size, offset_y, 
                        offset_x + i * Configuration.side_size, offset_y + Configuration.scale_y * Configuration.side_size)
        
        # Horizontal lines
        for i in range(1, Configuration.scale_y):
            dc.DrawLine(offset_x, offset_y + i * Configuration.side_size, 
                        offset_x + Configuration.scale_x * Configuration.side_size, offset_y + i * Configuration.side_size)

        # Pain Grid
        dc.SetPen(wx.Pen(Configuration.Color_A, 1, wx.TRANSPARENT))
        for i in range(Configuration.scale_x):
            for j in range(Configuration.scale_y):
                if(dataStore.gridInfos[i, j] == GridStatus.initial):
                    #dc.SetBrush(wx.Brush(self.Color_background, wx.SOLID))
                    continue
                elif(dataStore.gridInfos[i, j] == GridStatus.pained_by_A):
                    dc.SetBrush(wx.Brush(Configuration.Color_A, wx.SOLID))
                elif(dataStore.gridInfos[i, j] == GridStatus.pained_by_B):
                    dc.SetBrush(wx.Brush(Configuration.Color_B, wx.SOLID))
                else:
                    raise Exception('invalid grid status!')                    
                dc.DrawRectangle(offset_x + i * Configuration.side_size + 1, offset_y + j * Configuration.side_size + 1, 
                         Configuration.side_size - 1, Configuration.side_size - 1)
        
        # Pain Robot
        dc.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        angle, adjust_x, adjust_y = self.getAngleAndAdjust(dataStore.direction_A)
        dc.DrawRotatedText ('↑', offset_x + dataStore.position_A[0] * Configuration.side_size + adjust_x, offset_y + dataStore.position_A[1] * Configuration.side_size + adjust_y, angle)
        angle, adjust_x, adjust_y = self.getAngleAndAdjust(dataStore.direction_B)
        dc.DrawRotatedText ('↑', offset_x + dataStore.position_B[0] * Configuration.side_size + adjust_x, offset_y + dataStore.position_B[1] * Configuration.side_size + adjust_y, angle)

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
            self.trainMenuItem.Enable(False)
            self.stopMenuItem.Enable(True)
        else:
            raise Exception("worker is running!")

    #----------------------------------------------------------------------
    def onTrain(self, event):
        if not self.worker:
            self.worker = WorkerThread(self)
            self.worker._is_train = True
            self.worker.start()
            self.startMenuItem.Enable(False)
            self.trainMenuItem.Enable(False)
            self.stopMenuItem.Enable(True)
        else:
            raise Exception("worker is training!")       

    #----------------------------------------------------------------------
    def onStop(self, event):
        if self.worker:
            self.worker.abort()
            self.worker = None
        else:
            raise Exception("worker is not running!")
        self.startMenuItem.Enable(True)
        self.trainMenuItem.Enable(True)
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
            self.trainMenuItem.Enable(True)
            self.stopMenuItem.Enable(False)        
        global dataStore
        dataStore.reset()
        self.Refresh()
    #----------------------------------------------------------------------
    def OnResult(self, event):
        self.Refresh()
        self.statusbar.SetStatusText('Simulation steps: %s' % event.data)
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