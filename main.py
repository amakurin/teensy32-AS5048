import visual as vs
import visual.graph as vsg

import math 
import wx
from utils import RawHIDDevice, TimeCounter
from struct import pack, unpack


CMD_START_SENSORS = 0
CMD_STOP = 1
CMD_OTP_ZERO = 2

class MainWindow(object):
    def __init__(self):
        self.hid = None
        self.sensor_data = [0., 0.]
        self.run_loop = None

        self.frame_rate_counter = TimeCounter()

        self.w = vs.window(menus=True, title="Motor rotation visualizer", x=0, y=0, width=1150, height=600)
        ######################################
        ### WINDOW CONTROLS ##################
        ######################################
        gbs_main = wx.GridBagSizer( 5, 5 )
        gbs_main.SetFlexibleDirection( wx.BOTH )
        gbs_main.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
        
        # Quaternion box #####################
        sbAngle = wx.StaticBoxSizer( wx.StaticBox( self.w.panel, wx.ID_ANY, u"Angle" ), wx.VERTICAL )
        fsAngle = wx.FlexGridSizer( 0, 2, 0, 0 )
        fsAngle.SetFlexibleDirection( wx.BOTH )
        fsAngle.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
        
        self.m_staticText11 = wx.StaticText( sbAngle.GetStaticBox(), wx.ID_ANY, u"Radians:", wx.DefaultPosition, wx.DefaultSize, 0 )
        fsAngle.Add( self.m_staticText11, 0, wx.ALL, 5 )
        self.m_st_angle_rad = wx.StaticText( sbAngle.GetStaticBox(), wx.ID_ANY, u"0.00000000", wx.DefaultPosition, wx.DefaultSize, 0 )
        fsAngle.Add( self.m_st_angle_rad, 0, wx.ALL, 5 )
        self.m_staticText13 = wx.StaticText( sbAngle.GetStaticBox(), wx.ID_ANY, u"Degrees:", wx.DefaultPosition, wx.DefaultSize, 0 )
        fsAngle.Add( self.m_staticText13, 0, wx.ALL, 5 )
        self.m_st_angle_deg = wx.StaticText( sbAngle.GetStaticBox(), wx.ID_ANY, u"0.00000000", wx.DefaultPosition, wx.DefaultSize, 0 )
        fsAngle.Add( self.m_st_angle_deg, 0, wx.ALL, 5 )        
        sbAngle.Add( fsAngle, 1, wx.EXPAND, 5 )
        
        gbs_main.Add( sbAngle, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 1 ), wx.EXPAND, 5 )
        
        # Frequency box #####################
        sbFrequency = wx.StaticBoxSizer( wx.StaticBox( self.w.panel, wx.ID_ANY, u"Frequency" ), wx.VERTICAL )
        
        fgSizer3 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer3.SetFlexibleDirection( wx.BOTH )
        fgSizer3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
        
        self.m_st_filtUpdate = wx.StaticText( sbFrequency.GetStaticBox(), wx.ID_ANY, u"Filter update:", wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer3.Add( self.m_st_filtUpdate, 0, wx.ALL, 5 )
        
        self.m_st_filterRate = wx.StaticText( sbFrequency.GetStaticBox(), wx.ID_ANY, u"0000Hz", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_st_filterRate.SetFont( wx.Font( 20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )
        self.m_st_filterRate.SetForegroundColour( wx.Colour( 0, 0, 160 ) )
        
        fgSizer3.Add( self.m_st_filterRate, 0, wx.ALL, 5 )
        
        self.m_st_frameUpdate = wx.StaticText( sbFrequency.GetStaticBox(), wx.ID_ANY, u"Frame update:", wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer3.Add( self.m_st_frameUpdate, 0, wx.ALL, 5 )
        
        self.m_st_frameRate = wx.StaticText( sbFrequency.GetStaticBox(), wx.ID_ANY, u"000Hz", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_st_frameRate.SetFont( wx.Font( 20, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial" ) )
        self.m_st_frameRate.SetForegroundColour( wx.Colour( 100, 82, 74 ) )
        
        fgSizer3.Add( self.m_st_frameRate, 0, wx.ALL, 5 )
               
        sbFrequency.Add( fgSizer3, 1, wx.EXPAND, 5 )
        
        gbs_main.Add( sbFrequency,  wx.GBPosition( 0, 1 ), wx.GBSpan( 1, 1 ), wx.EXPAND, 5 )

        # Main layout #####################
        
        gbs_main.AddGrowableCol( 0 )
        gbs_main.AddGrowableCol( 1 )

        self.w.panel.SetSizer( gbs_main )
        self.w.panel.Layout()

        # Main Menu #####################
        self.m_menubar      = wx.MenuBar( 0 )
        self.m_menu_main    = wx.Menu()
        self.m_mi_setzero  = wx.MenuItem( self.m_menu_main, wx.ID_ANY, u"Set Zero", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu_main.AppendItem( self.m_mi_setzero )
        self.m_mi_start     = wx.MenuItem( self.m_menu_main, wx.ID_ANY, u"Start Vis", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu_main.AppendItem( self.m_mi_start )
        self.m_mi_stop      = wx.MenuItem( self.m_menu_main, wx.ID_ANY, u"Stop Vis", wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu_main.AppendItem( self.m_mi_stop )

        self.m_menubar.Append( self.m_menu_main, u"Tasks" ) 
        
        self.w.win.SetMenuBar( self.m_menubar)
        
        # Bind Events ########################################################################################
 
        self.w.win.Bind( wx.EVT_CLOSE , self.win_mainClose    , id = self.w.win       .GetId() )

        self.w.win.Bind( wx.EVT_MENU  , self.mi_setzeroClick  , id = self.m_mi_setzero.GetId() )
        self.w.win.Bind( wx.EVT_MENU  , self.mi_startClick    , id = self.m_mi_start  .GetId() )
        self.w.win.Bind( wx.EVT_MENU  , self.mi_stopClick     , id = self.m_mi_stop   .GetId() )
        

        # Plot ###############################################################################################
        self.plot=vsg.gdisplay(window=self.w, x=360, y=134, width=800, height=350, background=vs.color.black)
        self.xs = vsg.gcurve(color=(190./255.,  20./255.,   0./255.), dot=True, size=4)
        self.frame_counter = 0

        # 3D scene ###########################################################################################

        self.scene=vs.display(window=self.w, x=5, y=134, width=350, height=350, center=(0,10,0))

        self.scene.range=13

        self.axis = (1, 0, 0)

        self.f = vs.frame(pos = (0, 10, 0), axis =self.axis, up=(0, 1, 0))

        col_x = vs.color.red
        col_y = vs.color.green
        col_z = vs.color.blue

        axis_len = 3
        # X = vpyZ
        self.lblX = vs.label(frame=self.f, pos=(axis_len*1.05,0,0), text='X', box=0, opacity=0, color=col_x)
        self.arrX = vs.arrow(frame=self.f, pos=(0,0,0), axis=(1,0,0), shaftwidth=0.2, fixedwidth=1, length = axis_len, color=col_x)
        # Y = vpyX
        self.lblY = vs.label(frame=self.f, pos=(0,axis_len*1.05,0), text='Y', box=0, opacity=0, color=col_y)
        self.arrY = vs.arrow(frame=self.f, pos=(0,0,0), axis=(0,1,0), shaftwidth=0.2, fixedwidth=1, length = axis_len, color=col_y)
        # Z = vpyY
        self.lblZ = vs.label(frame=self.f, pos=(0,0,axis_len*1.05), text='Z', box=0, opacity=0, color=col_z)
        self.arrZ = vs.arrow(frame=self.f, pos=(0,0,0), axis=(0,0,1), shaftwidth=0.2, fixedwidth=1, length = axis_len,color=col_z)
        # Model
        self.motor = vs.cylinder(frame=self.f, pos=(0,0,0), axis=(0, 0, 1.5), radius=4.5, color=(0.5, 0.5, 0.5), opacity=0.7)
        self.mot_box1 = vs.box(frame=self.f, pos=(0.0, 0, 1.0), length=1, height=9, width=1.5, color=(0, 0, 0))
        self.mot_box2 = vs.box(frame=self.f, pos=(0.0, 0, 1.0), length=9, height=1, width=1.5, color=(0, 0, 0))
        self.platform = vs.box(pos=(0.0, 5, 0.0), length=5, height=10, width=0.2, color=(1,1,1), opacity=0.9)
        self.platform_leg = vs.box(pos=(0.0, 0, 2), length=5, height=0.2, width=4, color=(1,1,1), opacity=0.9)
        
        self.realtime_started = False

    def win_mainClose(self, event):
        if self.hid:
            self.hid.call(CMD_STOP, [], self.CMD_STOP_SENSORS_callback)
            self.hid.close()
        self.run_loop = False
        event.Skip()

    def mi_setzeroClick(self, event ) :
        self.hid.call(CMD_STOP, [], self.CMD_STOP_SENSORS_callback)
        self.clear_plot()

    def mi_startClick(self, event ) :
        self.realtime_started = True
        self.frame_rate_counter.reset()
        self.hid.call(CMD_START_SENSORS, [100, 0], self.CMD_START_SENSORS_callback)

    def mi_stopClick(self, event ) :
        self.hid.call(CMD_STOP, [], self.CMD_STOP_SENSORS_callback)
        self.clear_plot()

    def CMD_START_SENSORS_callback(self, hid, byte_response):
        self.sensor_data = unpack('f' * 2, str(bytearray(byte_response)))  

    def CMD_STOP_SENSORS_callback(self, hid, byte_response):
        hid.releaseCallback(CMD_START_SENSORS)
        self.realtime_started = False

    def clear_plot(self):
        if self.plot:
            for obj in self.plot.display.objects: 
                if obj.__class__.__name__ in ['curve', 'points']:
                    obj.visible = False
                    del obj
        self.xs = vsg.gcurve(color=(190./255.,  20./255.,   0./255.), dot=True, size=4)
        self.frame_counter = 0.

    def updateAngleLabels(self):
        self.m_st_angle_rad.SetLabelText('%+8f'%self.sensor_data[0]) 
        self.m_st_angle_deg.SetLabelText('%+8f'%math.degrees(self.sensor_data[0])) 

    def updateFrequencyLabels(self):
        self.frame_rate_counter.update()
        self.m_st_filterRate.SetLabelText('%04.0fHz'%self.sensor_data[-1])
        self.m_st_frameRate.SetLabelText('%03.0fHz'%self.frame_rate_counter.getRate())

    def plot_sensor_data(self):
        self.frame_counter += 1.
        self.xs.plot(pos=(self.frame_counter,self.sensor_data[0]))

    def update(self):
        if self.realtime_started:
            self.updateFrequencyLabels()
            self.updateAngleLabels()
            angle = self.sensor_data[0]
            self.f.axis = [ self.axis[0]*math.cos(angle) - self.axis[1]*math.sin(angle),
                            self.axis[0]*math.sin(angle) + self.axis[1]*math.cos(angle),
                            self.axis[2]] 
            self.plot_sensor_data()

    def loop(self):
        while not self.hid:
            self.hid = RawHIDDevice.tryOpen()
            if not self.hid:
                print "USB HID Device wasn't found. Retry in 5 seconds..."
                vs.sleep(5)
        print "USB HID Device found."
        self.run_loop = True
        while self.run_loop:
            self.update()
            vs.sleep(1E-2)  


def main():
    w = MainWindow()
    w.loop()
    
if __name__ == '__main__':
    main()
