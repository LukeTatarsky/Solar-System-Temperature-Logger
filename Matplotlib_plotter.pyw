'''
------------------------------------------------------------------------
Graphing program that reads the DS18B20 database on the network.
pysimplegui lets you select the time frame to view. Either live graph or static.
Animate function gets the data within the time frame. creates lists to provide Matplotlib.
Matplotlib creates a few graphs.

plans:
    
    - can create a cache db, copy it all over to local drive, then only grab new rows..
    
    - make an option to view week by getting avgs
    
    - allow for back and forth movement between time intervals  (done)
    
------------------------------------------------------------------------
Author: Luke Tatarsky
__created__ = "2021-02-13"
__updated__ = "2023-02-03"
------------------------------------------------------------------------
'''
import matplotlib.pyplot as plt
import sqlite3, time, numpy as np
import PySimpleGUI as sg
from datetime import datetime, timedelta

# Constants
TITLE_FONT_SIZE = 15
TITLE_ROUNDING = 1
XTICK_SIZE = 10.6
YTICK_SIZE = 12
#SLOPE_MULTIPLIER = 6.05
NUM_OF_SENSORS = 9

t = []

# for the next db reader, make an option to walk week by week or day by day.
fig, a = plt.subplots(3, 1)
fig.set_figwidth(14)
fig.set_figheight(12)

# adjust the spacing between subplots
fig.subplots_adjust(left=0.044, bottom=0.044, right=0.99, top=0.977, wspace=0.2, hspace=0.143)

def animate(start_time, end_time):
    '''
    ------------------------------------------------------
    Gets data from sqlite database. Processes data into lists to provide matplotlib.
    Matplotlib graphs the data.
    ------------------------------------------------------
    inputs are datetime objects

    returns data retrieval time
            data processing time
            last update time
    ------------------------------------------------------
    '''
    try:
        # LAN Remote database
        #conn = sqlite3.connect('//192.168.100.180/PiShare/shared_data.db')
        # WLAN Remote database
        #conn = sqlite3.connect('//192.168.100.181/PiShare/shared_data.db')
        # Local database
        conn = sqlite3.connect('D:/Eclipse Workspace 164/Raspberry Pi Temperature Logger/src/shared_data.db')
        c = conn.cursor()
    except:
        print ('___ERROR___ Could not connect to data, check network connection\n\
                Trying to connect to local db.')
        conn = sqlite3.connect('shared_data.db')
        c = conn.cursor()
    
    # create time string from current time
    #time_now = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # testing
    #t_time2 = datetime.now() # connected       for processing calc
    # convert string to datetime object
    #dt_time = datetime.fromisoformat(time_now)
    
    # testing print
    #print('\nCurrent Time:', time_now)

    date_l = list()
    time_l = list()
    glycol_in = list()
    glycol_out = list()
    solar_high = list()
    solar_mid = list()
    solar_low = list()
    solar_lowest = list()
    boiler_mid = list()
    boiler_out = list()
    solar_out = list() 
    # sqlite call needs a tuple
    
    # get all data between dates
    y = (start_time,end_time)
    c.execute('SELECT * FROM temperature WHERE Date_Time BETWEEN ? AND ?;', y)
    
    #c.execute('SELECT * FROM temperature WHERE Date_Time BETWEEN ? AND ? AND solar_high > 50;', y)
    try:
        x = c.fetchall()
    except:
        file = open('errors.txt', 'a+')
        file.write('{} error on fetchall comand\n'.format(datetime.now()))
        file.close()
        time.sleep(10)
        x = c.fetchall()
    conn.close()
    
    #t_time3 = datetime.now() # data recieved     for processing calc
    
    # populate the lists
    for i in x:
        i = list(i)
        # grab the date. we only need time for now. only the latest date is kept.
        date = (i[0].split(' '))[0]
        date_l.append(date)
        # isolate time
        i[0] = (i[0].split(' '))[1]
        time_l.append(i[0])
        glycol_in.append(i[1])
        glycol_out.append(i[2])
        solar_high.append(i[3])
        solar_mid.append(i[4])
        solar_low.append(i[5])
        solar_lowest.append(i[6])
        boiler_mid.append(i[7])
        boiler_out.append(i[8])
        solar_out.append(i[9])

    # doesnt really save much time. try more
    time_l = np.array(time_l)
    glycol_in = np.array(glycol_in)
    solar_mid = np.array(solar_mid)
    glycol_out = np.array(glycol_out)
    
# Graph setup
    if len(time_l) >= 5:
        # get the total time span for the graph        
        t1 = '{} {}'.format(date_l[0], time_l[0])
        dt1 = datetime.fromisoformat(t1)         # first date time in retrieved data
        t2 = '{} {}'.format(date_l[-1], time_l[-1])
        dt2 = datetime.fromisoformat(t2)      # last date time in retrieved data
        span = dt2-dt1
        
        # testing print
        #print('Last Update:  {}'.format(dt2))        
        #print('# of ticks: {}  |  Time Span: {}'.format(len(time_l),span))
        
# subplot 0  , glycol in/out
        
        a[0].clear()
        a[0].set_title('Glycol In: {}    |    Glycol Out: {}    |    In - Out: {}  |  Mid - Low: {}'
         .format( round(glycol_in[-1], TITLE_ROUNDING), round(glycol_out[-1], TITLE_ROUNDING), round(glycol_in[-1]-glycol_out[-1], TITLE_ROUNDING), round(solar_mid[-1]-solar_low[-1], TITLE_ROUNDING)), fontsize=TITLE_FONT_SIZE)
        
        a[0].set_xticks([0, len(time_l)//5, (len(time_l)//5)*2, (len(time_l)//5)*3,(len(time_l)//5)*4, len(time_l)-1])
        
        #a[0].plot(ar_t,ar06, label='Panel High', color='#228B22')
        a[0].plot(time_l, glycol_in, label='Glycol In', color='#cc0249')
        a[0].plot(time_l, solar_mid, label='Solar T Mid', color='#D84315')
        a[0].plot(time_l, glycol_out, label='Glycol Out', color='#004e92')
        
        a[0].legend(loc='lower left')
        
# subplot 1  ,  Solar Tank Temperatures, high, mid, low, lowest
        a[1].clear()
        a[1].set_title('Solar Tank         High: {}   |   Mid: {}   |   Low: {}   |   Lowest: {}'.format(
            round(solar_high[-1], TITLE_ROUNDING), round(solar_mid[-1], TITLE_ROUNDING), round(solar_low[-1], TITLE_ROUNDING), round(solar_lowest[-1], TITLE_ROUNDING)), fontsize=TITLE_FONT_SIZE)
        
        a[1].set_xticks([0, len(time_l)//5, (len(time_l)//5)*2, (len(time_l)//5)*3,(len(time_l)//5)*4, len(time_l)-1])
        
        a[1].plot(time_l,solar_high, label='High', color='#cc0249')
        a[1].plot(time_l,solar_mid, label='Mid', color='#D84315')
        a[1].plot(time_l,solar_low, label='Low', color='#0097A7')
        a[1].plot(time_l,solar_lowest, label='Lowest', color='#004e92')
        
        a[1].legend(loc='lower left')

# subplot 2  ,  Boiler out, solar tank out, Boiler mid, Room temp
        a[2].clear()
        a[2].set_title('Boiler Tank Mid: {}    |    Boiler t Out: {}    |    Solar t Out: {}'\
        .format(round(boiler_mid[-1], TITLE_ROUNDING), round(boiler_out[-1],TITLE_ROUNDING), round(solar_out[-1],TITLE_ROUNDING)), fontsize = TITLE_FONT_SIZE)
        
        a[2].set_xticks([0, len(time_l)//5, (len(time_l)//5)*2, (len(time_l)//5)*3,(len(time_l)//5)*4, len(time_l)-1])
        a[2].set_ylabel(('Temp *C'), fontsize = TITLE_FONT_SIZE-1)
        a[2].set_xlabel('Time Span: {}      |     {}'.format(span, dt2.strftime('%A, %B %d, %Y')), fontsize = TITLE_FONT_SIZE)
        a[2].plot(time_l,solar_high, label='Solar T High', color='#cc0249')
        a[2].plot(time_l,boiler_mid, label='Boiler T Mid', color='#44007d')
        a[2].plot(time_l,boiler_out, label='Boiler T Out', color='#F06292')        
        a[2].plot(time_l,solar_out, label='Solar T Out', color='#66BB6A')
         
        a[2].legend(loc='lower left')

        # enable grids
        a[0].grid(True)
        a[1].grid(True)
        a[2].grid(True)
        

        a[0].tick_params(axis='x',labelsize=XTICK_SIZE)
        a[1].tick_params(axis='x',labelsize=XTICK_SIZE)
        a[2].tick_params(axis='x',labelsize=XTICK_SIZE)
        a[0].tick_params(axis='y',labelsize=YTICK_SIZE)
        a[1].tick_params(axis='y',labelsize=YTICK_SIZE)
        a[2].tick_params(axis='y',labelsize=YTICK_SIZE)
    
   #  dt2  last date time in retrieved data
    #return t_time2,t_time3,dt2
    
    return dt2
    
def graph_refresh(start_t, end_t):
    '''
    simply calls the animate function with a new start and end time.
    inputs are datetime objects
    returns last update time
    '''
    
    #t_time1 = datetime.now()    # to get processing time
    #t_time2, t_time3, dt2 = animate(start_t, end_t)
    dt2 = animate(start_t, end_t)
    fig.canvas.draw()
    #t_time4 = datetime.now() # graphed    # to get processing time
    #time_log = open('time_log.csv', 'a+')
    #time_log.write('_{},_{},_{},_{},_{}\n'.format(t_time3-t_time2, t_time4-t_time3, t_time4-t_time1,end_t-start_t, t_time1))
    #time_log.close()
    #print('\ndata retrieval {} \nprocessing     {}\n{}\nrefresh time   {}\n'.format(t_time3-t_time2, t_time4-t_time3, '-'*29, t_time4-t_time1))
    return dt2

def show_hour(end_time):
    '''
    run this when the show hour graph button is clicked
    returns last update time
    '''
    values['_refresh'] = 'Automatic Refresh - Disabled'
    window['_showhour'].update('Show Static Graph')
    window['_live'].update('Show Live Graph')
    window['_TEXT'].update('Viewing Static Graph\nShowing last   {} hours.  \n{}'.format(int(values['_hours']),values['_refresh']))
    #end_time = datetime.now()
    start_time = end_time - timedelta(hours = int(values['_hours']))
    dt2 = graph_refresh(start_time, end_time)
    return dt2

width = 430
height = 430

sg.theme('DarkAmber')   # Add a touch of color
# Hour Slider
slider1 = {'range': (1,24), 'resolution': 1, 'default_value': 24,
     'size': (20,15), 'orientation': 'horizontal',
     'font': ('Helvetica', 8), 'enable_events': False}
# refresh slider
slider2 = {'range': (45,240), 'resolution': 1, 'default_value': 120,
     'size': (20,15), 'orientation': 'horizontal',
     'font': ('Helvetica', 8), 'enable_events': False}
'''
layout = [  [sg.Text('Select how many hours to display', key='_TEXT', size=(width,3))],
            [sg.Text('          Hours:'), sg.Slider(**slider1, key='_hours')],
            [sg.Text('Live Refresh Interval:'), sg.Slider(**slider2, key='_refresh')],
            [sg.Button('Show Hour Graph', key='_showhour', font=('MS Sans Serif', 10, 'bold')),\
                sg.Button('Show Live Graph', key='_live', font=('MS Sans Serif', 10, 'bold'))], 
            [sg.Text('          ')],      
            [sg.Text('Start Date: ________', key='_cs', size=(width//2,1))],
            [sg.Text('End  Date: ________', key='_ce', size=(width//2,1))], 
            [sg.In('', key='_break', enable_events=True, visible=False),],
            [sg.In(key='_cal_start', enable_events=True, visible=False), sg.CalendarButton('Calendar Start', target='_cal_start', font=('MS Sans Serif', 10, 'bold')),\
             sg.In(key='_cal_end', enable_events=True, visible=False), sg.CalendarButton('Calendar End', target='_cal_end', font=('MS Sans Serif', 10, 'bold'))],
            [sg.Button('Show Calendar Graph', key='_showcal', font=('MS Sans Serif', 10, 'bold'))],
            [sg.Button('Exit')],]
'''
layout = [  [sg.Text('Select how many hours to display', key='_TEXT', size=(width,4), font=('MS Sans Serif', 11))],
            [sg.Text('Current time: {}'.format(time.strftime('%H:%M:%S')), key='_TEXT2', size=(width,1), font=('MS Sans Serif', 11))],
            [sg.Text('Last update:', key='_LASTUP', size=(width,1), font=('MS Sans Serif', 11))],
            [sg.Text('                Hours:', font=('MS Sans Serif', 10)), sg.Slider(**slider1, key='_hours')],
            [sg.Text('Live Refresh Interval:', font=('MS Sans Serif', 10)), sg.Slider(**slider2, key='_refresh')],
            [sg.Button('Show Static Graph', key='_showhour', enable_events=True , font=('MS Sans Serif', 10, 'bold')),\
                sg.Button('Show Live Graph', key='_live', enable_events=True , font=('MS Sans Serif', 10, 'bold'))], 
            [sg.Text('          ')],      
            [sg.In('', key='_break', enable_events=True, visible=False),],
            [sg.Button('Exit', font=('MS Sans Serif', 10, 'bold')), sg.Text('       '), 
            sg.Button('Previous', key='_previousbtn', enable_events=True, visible=False , font=('MS Sans Serif', 10, 'bold')),
            sg.Button('Refresh', key='_liveRefreshbtn', enable_events=True, visible=False , font=('MS Sans Serif', 10, 'bold')),
            sg.Button('Refresh', key='_staticRefreshbtn', enable_events=True, visible=False , font=('MS Sans Serif', 10, 'bold')),
            sg.Button('Next', key='_nextbtn', enable_events=True, visible=False , font=('MS Sans Serif', 10, 'bold'))],]


    
# Create the Window
window = sg.Window('Solar System Temperature', layout, size=(width, height))
dt_time = None
while True:
    '''
    while loop for the gui
    '''
    event, values = window.read(timeout=100)
    window['_TEXT2'].update('Current time: {}'.format(time.strftime('%H:%M:%S')))
    # Event Loop to process "events" and get the "values" of the inputs
    
    if dt_time == None:
        dt_time = datetime.now()
    start_time = dt_time - timedelta(hours = int(values['_hours']))
    end_time = dt_time
    #window['_TEXT2'].update('last refresh: {}'.format(time.strftime('%H:%M:%S')))
    
    
    if event == sg.WIN_CLOSED or event == 'Exit': # if user closes window or clicks cancel
        break
    # strip the time from the start date.
    elif event == '_cal_start':
        values['_cal_start'] = values['_cal_start'].split()[0] + ' 00:00:00'
        cal_start = values['_cal_start'].split()[0]
        window['_cs'].update('Start Date: {}'.format(cal_start + '  00:00:00'))
        
    elif event == '_cal_end':
        values['_cal_end'] = values['_cal_end'].split()[0] + ' 23:59:59'
        cal_end = values['_cal_end'].split()[0]
        window['_ce'].update('End  Date: {}'.format(cal_end + '  23:59:59'))
        
    elif event == '_showhour':
        window['_staticRefreshbtn'].update(visible=True) 
        window['_previousbtn'].update(visible=True)
        window['_nextbtn'].update(visible=True)          
        dt_time = show_hour(datetime.now())
        window['_LASTUP'].update('Last Update: {}'.format(str(dt_time)[-8:]))
        plt.pause(.01)
        
    elif event == '_previousbtn':
        end_time = end_time - timedelta(hours = int(values['_hours']))
        dt_time = show_hour(end_time)
        plt.pause(.01)
       
    elif event == '_nextbtn':
        end_time = end_time + timedelta(hours = int(values['_hours']))
        if end_time > datetime.now():
            end_time = datetime.now()
        dt_time = show_hour(end_time)
        plt.pause(.01)
        
    elif event == '_liveRefreshbtn':
        end_time = datetime.now()
        start_time = end_time - timedelta(hours = int(values['_hours']))
        dt2 = graph_refresh(start_time, end_time)
        window['_TEXT'].update('Viewing Static Graph\nShowing last -  {} hours.  \nAutomatic Refresh - Disabled.'.format(int(values['_hours']),int(values['_refresh'])))
        window['_LASTUP'].update('Last Update: {}'.format(str(dt2)[-8:]))
    
    elif event == '_staticRefreshbtn':
        #end_time = datetime.now()
        start_time = end_time - timedelta(hours = int(values['_hours']))
        dt_time = graph_refresh(start_time, end_time)
        window['_TEXT'].update('Viewing Static Graph\nShowing last -  {} hours.  \nAutomatic Refresh - Disabled.'.format(int(values['_hours']),int(values['_refresh'])))
        window['_LASTUP'].update('Last Update: {}'.format(str(dt_time)[-8:]))
        
    elif event == '_live':
        values['_break'] = ''
        window['_liveRefreshbtn'].update(visible=True)
        window['_staticRefreshbtn'].update(visible=False)
        window['_previousbtn'].update(visible=False)
        window['_nextbtn'].update(visible=False)
        
        while values['_break'] == '':
            # marker is to stop graph refresh from being done twice when you click refresh
            marker = False
            window['_live'].update('Pause Live Graph')
            window['_showhour'].update('Show Static Graph')
            window['_TEXT'].update('Viewing Live Graph\nShowing last -  {} hours.  \nAutomatic Refresh - {} seconds.\n...Waiting for refresh'.format(int(values['_hours']),int(values['_refresh'])))
            end_time = datetime.now()
            start_time = end_time - timedelta(hours = int(values['_hours']))
            if marker == False:
                dt2 = graph_refresh(start_time, end_time)
            
            #print('waiting - {}'.format(int(values['_refresh'])))
            window['_TEXT2'].update('Last Refresh: {}'.format(time.strftime('%H:%M:%S')))
            window['_LASTUP'].update('Last Update: {}'.format(str(dt2)[-8:]))
            plt.pause(0.01)
            time.sleep(0.01)
            interval = int(values['_refresh']) - 3
            marker = True
            event, values = window.read(timeout=interval*1000)
            
            if event == '_showhour' or event == 'Exit' or event == '_live':
                values['_break'] = 'stop'                
                if event == '_showhour':
                    show_hour(datetime.now())
                    window['_liveRefreshbtn'].update(visible=False)
                    window['_staticRefreshbtn'].update(visible=True)
                    window['_previousbtn'].update(visible=True)
                    window['_nextbtn'].update(visible=True)
                    
                    
                else:
                    window['_live'].update('Show Live Graph')
                    window['_showhour'].update('Show Static Graph')
                    
                    window['_TEXT'].update('PAUSED\nShowing last -  {} hours.  \nAutomatic Refresh - Disabled.'.format(int(values['_hours']),int(values['_refresh'])))
            if event == '_liveRefreshbtn':
                marker = True
                window['_TEXT2'].update('Last Refresh: {}'.format(time.strftime('%H:%M:%S')))
                window['_LASTUP'].update('Last Update: {}'.format(str(dt2)[-8:]))
                window['_TEXT'].update('\nShowing last -  {} hours.  \nAutomatic Refresh - Disabled.'.format(int(values['_hours']),int(values['_refresh'])))

        # makes the button dissapear when the while loop is done.
        #window['_refreshbtn'].update(visible=False)    
    elif event == '_showcal':
        try:
            # check that start date is before end date
            t1 = datetime.fromisoformat(values['_cal_start'])
            t2 = datetime.fromisoformat(values['_cal_end'])
            zer0 = datetime.now() - datetime.now()
            
            values['_refresh'] = 999
            if values['_cal_start'] != '' and values['_cal_end'] != '' and t2-t1 > zer0:
                window['_TEXT'].update('Showing {} to {} \nRefresh every  {} seconds.'.format(cal_start, cal_end, int(values['_refresh'])))
            graph_refresh(start_time, end_time)
            plt.pause(.01)
        except:
            window['_TEXT'].update('Error. Must select valid start and end date.')
    
    
window.close()

