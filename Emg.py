# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 16:29:54 2020
@author: danoc
"""
"""
Criacao Multiprocessamento 06/03/21 2021
@author of multiprocessing: Tsimoes
"""
import socket
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.widgets import Button
import json
from scipy import signal
from scipy.ndimage.interpolation import shift
import time

#plt.rc('text', usetex=True)

######################################
#Initial parameters

#HOST = socket.gethostbyname(socket.gethostname())
HOST = '192.168.4.1'  # Manual host enter
PORT = 80  # Port

fs = 1000 #Sampling frequency
f0 = 60  #Notch filter frequency
Q = 5 #Quality factor (Notch Filter)
fL = 5 #Low frequency (band-pass filter)
fH = 450 #High frequency (band-pass filter)

rms = 0 #RMS feature
F = 1 #number of sub-windows to divide the buffer
th = 0.1 #0.0135 #initial threshold
#time_range = 4 #time range to plot
buffer_size = 64 #size of the received buffer


            

#define the plot size
#plot_size = int(time_range*fs*F/buffer_size)

######################################
#Create filters
bf, af = signal.iirnotch(f0, Q, fs)
b1h, a1h = signal.iirnotch(2*f0, Q, fs)
b2h, a2h = signal.iirnotch(3*f0, Q, fs)
b, a = signal.iirfilter(4, [2*fL/fs, 2*fH/fs],
                        btype='band', analog=False, ftype='butter')
######################################

######################################
# Create plot area
amp = 0.9 #plot limit (y-axis)
plt.ion()
#data_array = np.zeros(plot_size)+0.1
#fig, = plt.plot(data_array)


fig, ax = plt.subplots()

fig, =plt.bar(1,th,color='royalblue')


plt.tick_params(
    axis='x',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    bottom=False,      # ticks along the bottom edge are off
    top=False,         # ticks along the top edge are off
    labelbottom=False) # labels along the bottom edge are off

plt.rcParams['font.size'] = '16'
for label in (ax.get_xticklabels() + ax.get_yticklabels()):
	label.set_fontsize(12)

plt.ylabel('EMG amplitude', fontsize=14)

canvas= plt.gcf()
canvas.set_size_inches(5, 5)     # set a suitable size

#Canvas setup
c_right=0.8
c_left=0.125
c_bottom=0.1
c_top=0.9
plt.subplots_adjust(right=c_right)
plt.subplots_adjust(left=c_left)
plt.subplots_adjust(bottom=c_bottom)
plt.subplots_adjust(top=c_top)

#plt.tight_layout()

th_line = plt.axhline(th, color='r', linestyle='-')
ax = plt.ylim((0,amp))
######################################

######################################
# Create Slider to choose threshold
v0 = 0

#adjust the slider to match the canvas
b_width = 0.08
b_left = c_right+(1-c_right-b_width)/2
b_bottom = c_bottom
b_height = c_top-c_bottom

axb = plt.axes([b_left, b_bottom, b_width, b_height])
sb = Slider(axb, 'Th.', 0.00, amp, valinit=v0, orientation='vertical')
######################################


######################################
# Create Button

btn_width = 0.2
btn_height = 0.075

btn_bottom = c_top+(1-c_top-btn_height)/2
btn_left1 = c_left
btn_left2 = c_right-btn_width

axprev = plt.axes([btn_left1, btn_bottom, btn_width, btn_height])
axnext = plt.axes([btn_left2, btn_bottom, btn_width, btn_height])
bnext = Button(axnext, 'Up')
bprev = Button(axprev, 'Down')

#Index value text
t_xpos = (c_right-c_left)/2+c_left
t_ypos = btn_bottom+btn_height/2

ind_text = plt.text(t_xpos, t_ypos,5, size = 15,
                    transform=plt.gcf().transFigure,
                    ha="center", va="center",
                    bbox=dict(facecolor='red', 
                              alpha=0.5,
                              boxstyle="round",
                              ec=(1., 0.5, 0.5),
                              fc=(1., 0.8, 0.8),
                              )
                    )


######################################

######################################
# Stream parameters
N = 5 #Number of buffers to concatenate
stream = np.zeros(N*buffer_size) #create empty stream vector
######################################

#plt.pause(1)

######################################
# Functions
######################################


#Button index class
class Index(object):
    ind = 0
    
    def set_ind(self, ind_val):
        self.ind = ind_val

    def up(self, event):
        self.ind += 1
        
    def down(self, event):
        self.ind -= 1
        
        if self.ind<0:
            self.ind = 0

#Function to update the threshold
def update(val):
    global th
    th = val
    th_line.set_ydata(th)
    

#Function to plot the data (and update)
def plotdata(data):
    global data_array

    sb.on_changed(update)    
   #fig.set_ydata(np.append(fig.get_ydata()[len(data):], data))
    fig.set_height(data)
    plt.draw()    
    plt.pause(0.01)
    
#Function to create the data stream
# x: income data
# y: data stream    
def addtoStream(x,y):      
    y = shift(y,len(x))
    y[0:len(x)]=x
    return y

#Function to calculate rms value
    # data: EMG buffer
    # N: number of sub-windows
def rmsVector(data,N):
    rms = np.zeros(N)
    ndata = np.array_split(data,N)
    for i in range(len(ndata)):
        y = ndata[i]
        rms[i] = np.sqrt(np.mean(y**2))
    return rms
    



#Main function
def connected(c):
    
    global data, msg, rms, stream, fig

    ind_value = 5 #button index value
    button_flag =""
    sch_trigger = 0
    th_on = "a"
    th_off = "b"
    msg_end = " \n"

    while True:
        
        new_ind = callback.ind
        
        if new_ind > ind_value:
            button_flag = "d"
        elif new_ind < ind_value:
            button_flag = "s"
        else:
            button_flag = ""
        
        ind_value = new_ind
        
        ind_text.set_text(str(ind_value))
        #print(callback.ind)   

        msg = c.recv(4096) #receive data...
        

        #if not msg: break
        if msg is not None:
            #print('zip')

            #Convert the data arriving
            data_msg = json.loads(msg)
            #print(data_msg)
            #print(time.time())
            #Filter the data
            y = signal.filtfilt(bf, af, data_msg)
            y = signal.filtfilt(b1h, a1h, y)
            y = signal.filtfilt(b2h, a2h, y)
            y = signal.filtfilt(b, a, y)
            stream = addtoStream(y,stream)
           
            #Calculate the RMS
            rms = rmsVector(stream,F)
            #print(rms)
            #Plot data
            plotdata(rms)
            #print(rms)       
            #print("------")
            #rms = 0.2
            #compare data to the threshold...
            #and encode a mensage to send.
            

            if np.mean(rms)>th: 
                
                
                
                fig.set_color('tomato')
                #c.send((th_on+str(ind_value)+msg_end).encode()) 
                #c.send((th_on+msg_end).encode())
                if sch_trigger < 1:
                    c.send((th_on+button_flag+msg_end).encode()) 
                    sch_trigger = 1
                else:
                    c.send((th_off+button_flag+msg_end).encode()) 
                
            else:
                fig.set_color('royalblue')
                #c.send((th_off+str(ind_value)+msg_end).encode())
                #c.send((th_off+msg_end).encode())
                c.send((th_off+button_flag+msg_end).encode()) 
                sch_trigger = 0
    #_thread.exit()
                


######################################
# Main Code
######################################
                
#Create Socket                
sock = socket.socket()
sock.connect((HOST, PORT))
#tcp.bind(orig)
#tcp.listen(1)

#Initial threshold value
update(th)

#Create index object to update the button
callback = Index()
callback.set_ind(5)
bnext.on_clicked(callback.up)
bprev.on_clicked(callback.down)

while True:
    try:
        #con, cliente = tcp.accept()
        #_thread.start_new_thread(connected, tuple([con, cliente]))
        
        #do things
        connected(sock)
    except Exception as e: pass#print(e)


sock.close()