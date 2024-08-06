'''
Class layout adapted from 
https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter/7557028#7557028
'''

import sys 

import tkinter as tk
import numpy as np
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from matplotlib import figure              #see self.fig, self.ax.

import matplotlib                          #I need this for matplotlib.use. sowwee.
matplotlib.use('TkAgg')                    #strange error messages will appear otherwise.

from tkinter import font as tkFont
from tkinter import messagebox
from tkinter import filedialog
import glob

import matplotlib.ticker as ticker
from PIL import Image, ImageChops

from skimage.filters import threshold_otsu

homedir = os.getenv('HOME')

#create main window container, into which the first page will be placed.
class App(tk.Tk):
    
    def __init__(self, path_to_repos, initial_browsedir, save_path, window_geometry, init_offset):  #INITIALIZE; will always run when App class is called.
        tk.Tk.__init__(self)     #initialize tkinter; *args are parameter arguments, **kwargs can be dictionary arguments
        
        self.title('Project Pixel: Generate Pixelated Images for Art')
        self.geometry(window_geometry)
        self.resizable(True,True)
        self.rowspan=10
        
        #will be filled with heaps of frames and frames of heaps. 
        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)     #fills entire container space
        container.grid_rowconfigure(0,weight=1)
        container.grid_columnconfigure(0,weight=1)

        ## Initialize Frames
        self.frames = {}     #empty dictionary
        frame = MainPage(container, self, path_to_repos, initial_browsedir, save_path, init_offset)   #define frame  
        self.frames[MainPage] = frame     #assign new dictionary entry {MainPage: frame}
        frame.grid(row=0,column=0,sticky='nsew')   #define where to place frame within the container...CENTER!
        for i in range(self.rowspan):
            frame.columnconfigure(i, weight=1)
            frame.rowconfigure(i, weight=1)
        
        self.show_frame(MainPage)  #a method to be defined below (see MainPage class)
    
    def show_frame(self, cont):     #'cont' represents the controller, enables switching between frames/windows...I think.
        frame = self.frames[cont]
        frame.tkraise()   #will raise window/frame to the 'front;' if there is more than one frame, quite handy.
        
#inherits all from tk.Frame; will be on first window
class MainPage(tk.Frame):    
    
    def __init__(self, parent, controller, path_to_repos, initial_browsedir, save_path, init_offset):
        
        #defines the number of rows/columns to resize when resizing the entire window.
        self.rowspan=10
        
        self.init_offset = float(init_offset)
        self.color = 'black'    #for gridlines
        
        #generalized parameters given in params.txt file
        self.path_to_repos = path_to_repos
        self.initial_browsedir = initial_browsedir
        self.save_path = save_path
        
        self.savefig_counter = 0     #will use for filenames! 
        
        #first frame...
        tk.Frame.__init__(self,parent)
        
        #create display frame!
        self.frame_display = tk.LabelFrame(self,text='Image',font='Vendana 15',padx=5,pady=5)
        self.frame_display.grid(row=0,column=0,rowspan=5)
        #include the following so that frame size adjusts correspondingly to window size
        for i in range(self.rowspan):
            self.frame_display.columnconfigure(i,weight=1)
            self.frame_display.rowconfigure(i,weight=1)
            
        #add the Browse/Refresh frame!
        self.frame_buttons=tk.LabelFrame(self,text='File Browser',padx=5,pady=5)
        self.frame_buttons.grid(row=0,column=1,columnspan=2)
        for i in range(self.rowspan):
            self.frame_buttons.columnconfigure(i,weight=1)
            self.frame_buttons.rowconfigure(i,weight=1)
        
        #create pixel parameter frame!
        self.frame_params = tk.LabelFrame(self,text='Parameters',padx=5,pady=5)
        self.frame_params.grid(row=1,column=1,sticky='e',columnspan=1)
        for i in range(self.rowspan):
            self.frame_params.columnconfigure(i,weight=1)
            self.frame_params.rowconfigure(i,weight=1)
        
        ##############
        #SPECIFY INITIATION FUNCTIONS.
        #(All functions are defined below this section.)
        ##############
        self.im_to_display()   #creates browse frame
        self.init_display_size()   #creates canvas frame
        self.populate_params()     #creates parameter frame
    
    #add trimming features!

    def trim_widgets(self):
        
        #pixel values > threshold set to white (255), pixels < threshold set to black (0)
        threshold_lab = tk.Label(self.frame_params,text='Trim Threshold',font='Arial 14')
        threshold_lab.grid(row=0,column=0,sticky='nsew',columnspan=2)
        
        self.threshold_val = tk.Entry(self.frame_params,width=5,borderwidth=2,
                                      bg='black',fg='lime green',font='Arial 15')
        self.threshold_val.insert(0,'1')
        self.threshold_val.grid(row=0,column=2,sticky='nsew',columnspan=1)
        
        self.trim_button = tk.Button(self.frame_params,text='Trim Preview',padx=2,pady=5,
                                     font='Arial 18', command=self.im_trim_preview)
        self.trim_button.grid(row=1,column=0,columnspan=4,sticky='ew')
        
        self.divider = tk.Label(self.frame_params,text='=============================================', 
                                font='Arial 11').grid(row=2,column=0,columnspan=4,sticky='ew')
    
    #add pixelation/resizing features
    def resize_widgets(self):
        
        self.trimvar = tk.BooleanVar()   #initiate variable
        
        npx_lab = tk.Label(self.frame_params,text='N Pixels',
                           font='Arial 19').grid(row=3,column=0)
        npx_lab = tk.Label(self.frame_params,text='(for x if x > y, y if y < x)',
                           font='Arial 12').grid(row=4,column=0)
        
        self.npx = tk.Entry(self.frame_params,width=5,borderwidth=2,bg='black',fg='lime green',font='Arial 15')
        self.npx.insert(0,'50')
        self.npx.grid(row=3,column=2,rowspan=2,sticky='w')
        
        ncolor_lab = tk.Label(self.frame_params,text='N Colors',
                              font='Arial 19').grid(row=5,column=0)
        ncolor_lab = tk.Label(self.frame_params,text='(Leave Blank for Default)',
                              font='Arial 12').grid(row=6,column=0)
        
        self.ncolor = tk.Entry(self.frame_params,width=5,borderwidth=2,bg='black',fg='lime green',font='Arial 15')
        self.ncolor.grid(row=5,column=2,rowspan=2,sticky='w')
   
        self.notrim_button = tk.Radiobutton(self.frame_params,text='No Image Trim',variable=self.trimvar,value=False)
        self.notrim_button.grid(row=7,column=0)
        
        self.trim_button = tk.Radiobutton(self.frame_params,text='Image Trim',variable=self.trimvar,value=True)
        self.trim_button.grid(row=8,column=0)
        
        self.pix_button_trim = tk.Button(self.frame_params,text="Pixelate", padx=4, pady=4, 
                                        font='Arial 20', command=self.resize_im)
        self.pix_button_trim.grid(row=7,column=1,rowspan=2,columnspan=3,sticky='nsew')
        
        self.divider = tk.Label(self.frame_params,text='=============================================', 
                                font='Arial 11').grid(row=9,column=0,columnspan=4,sticky='ew')
    
    def increment_px(self):
        npx_val = int(self.npx.get())
        npx_val += 1
        self.npx.delete(0,tk.END)
        self.npx.insert(0,str(npx_val))
        
        #automatically pixelate the image with this and other set parameters
        self.resize_im()

    def decrement_px(self):
        npx_val = int(self.npx.get())
        npx_val -= 1
        self.npx.delete(0,tk.END)
        self.npx.insert(0,str(npx_val))
        
        self.resize_im()
    
    def increment_col(self):
        try:
            ncol_val = int(self.ncolor.get())
        except:
            #if the user's input in this textbox is NONETYPE, then find the number of unique colors in
            #the image array and increment/decrement from there...
            #the following two lines are taken from self.im_trim()
            im_px = self.img_array.reshape(-1, self.img_array.shape[2])
            ncol_val = len(np.unique(im_px, axis=0, return_counts=False))
        ncol_val += 1
        self.ncolor.delete(0,tk.END)
        self.ncolor.insert(0,str(ncol_val))
        
        self.resize_im()
    
    def decrement_col(self):
        ncol_val = int(self.ncolor.get())
        ncol_val -= 1
        self.ncolor.delete(0,tk.END)
        self.ncolor.insert(0,str(ncol_val))
        
        self.resize_im()
        
    #please applaud my clever function name. three claps will do.
    def add_crement_buttons(self):
                
        self.incarrow_px = tk.Button(self.frame_params,text='+',padx=0.5,pady=0.5,font='Arial 16',
                                     command=self.increment_px)
        self.incarrow_px.grid(row=3,column=3,rowspan=2,sticky='w')
        
        self.decarrow_px = tk.Button(self.frame_params,text='-',padx=0.5,pady=0.5,font='Arial 16',
                                     command=self.decrement_px)
        self.decarrow_px.grid(row=3,column=1,rowspan=2,sticky='e')
        
        self.incarrow_col = tk.Button(self.frame_params,text='+',padx=0.5,pady=0.5,font='Arial 16',
                                      command=self.increment_col)
        self.incarrow_col.grid(row=5,column=3,rowspan=2,sticky='w')
                
        self.decarrow_col = tk.Button(self.frame_params,text='-',padx=0.5,pady=0.5,font='Arial 16',
                                      command=self.decrement_col)
        self.decarrow_col.grid(row=5,column=1,rowspan=2,sticky='e')

    #add grid checkbox to frame_params
    def grid_checkbox(self):
        
        self.var = tk.IntVar()   #initiate variable
        self.gridcheck = tk.Checkbutton(self.frame_params,text='Add Gridlines',
                                        onvalue=1,offvalue=0,command=self.add_grid,
                                        variable=self.var,font='Arial 18')
        self.gridcheck.grid(row=18,column=0,sticky='ew',columnspan=4)
    
    #add grid textbox to frame_params --> specify color of grid lines AND line spacing
    def grid_textbox(self):
        
        linespacing_lab = tk.Label(self.frame_params,text='Line Spacing',font='Arial 14')
        linespacing_lab.grid(row=14,column=0,sticky='nsew',columnspan=2)
        linethickness_lab = tk.Label(self.frame_params,text='Line Thickness',font='Arial 14')
        linethickness_lab.grid(row=15,column=0,sticky='nsew',columnspan=2)
        color_grid_lab = tk.Label(self.frame_params,text='Grid Color',font='Arial 14')
        color_grid_lab.grid(row=16,column=0,sticky='nsew',columnspan=2)
        offset_val_lab = tk.Label(self.frame_params,text='Offset Value',font='Arial 14')
        offset_val_lab.grid(row=17,column=0,sticky='nsew',columnspan=2)

        self.line_spacing = tk.Entry(self.frame_params,width=5,borderwidth=2,bg='black',fg='lime green',
                                      font='Arial 15')
        self.line_spacing.insert(0,'1')
        self.line_spacing.grid(row=14,column=2,sticky='nsew')
        
        self.line_thickness = tk.Entry(self.frame_params,width=5,borderwidth=2,bg='black',fg='lime green',
                                       font='Arial 15')
        self.line_thickness.insert(0,'1')
        self.line_thickness.grid(row=15,column=2,sticky='nsew')
        
        self.color_grid = tk.Entry(self.frame_params,width=5,borderwidth=2,bg='black',fg='lime green',
                                      font='Arial 15')
        self.color_grid.insert(0,'black')
        self.color_grid.grid(row=16,column=2,sticky='nsew')
        
        self.offset_val = tk.Entry(self.frame_params,width=5,borderwidth=2,bg='black',fg='lime green',
                                   font='Arial 15')
        self.offset_val.insert(0,str(self.init_offset))
        self.offset_val.grid(row=17,column=2,sticky='nsew')
        
        self.divider = tk.Label(self.frame_params,text='=============================================', 
                                font='Arial 11').grid(row=19,column=0,columnspan=4,sticky='ew')
        
    
    #add x-flip checkbox to frame_params
    def flip_checkbox(self):

        self.flipvar = tk.BooleanVar()   #initiate variable
        
        self.flipcheck = tk.Checkbutton(self.frame_params,text='Flip X-Axis',
                                        onvalue=True,offvalue=False,command=self.flip_xaxis,
                                        variable=self.flipvar,font='Arial 18')
        self.flipcheck.grid(row=11,column=0,sticky='ew',columnspan=4)
    
    def grayscale_box(self):
        self.grayvar = tk.BooleanVar()
        self.graycheck = tk.Checkbutton(self.frame_params,text='Convert to Grayscale',
                                        onvalue=True,offvalue=False,command=self.convert_grayscale,
                                        variable=self.grayvar,font='Arial 18')
        self.graycheck.grid(row=12,column=0,sticky='ew',columnspan=4)
        
        self.divider = tk.Label(self.frame_params,text='=============================================', 
                                font='Arial 11').grid(row=13,column=0,columnspan=4,sticky='ew')
    
    def save_image(self):
        
        while os.path.exists('{}{:d}-pxd.png'.format(self.save_path+self.filename, self.savefig_counter)):
            self.savefig_counter += 1
            filename = '{}{:d}-pxd.png'.format(self.save_path+self.filename,self.savefig_counter)
            self.fig.savefig(filename,dpi=100,bbox_inches='tight', pad_inches=0.2)
            print(f'Figure saved to: {filename}')
        else:
            filename = '{}{:d}-pxd.png'.format(self.save_path+self.filename,self.savefig_counter)
            self.fig.savefig(filename,dpi=100,bbox_inches='tight', pad_inches=0.2)
            print(f'Figure saved to: {filename}')
            
    def add_save_button(self):
        
        self.save_button = tk.Button(self.frame_params, text='Save Result', padx=5, pady=5, font='Ariel 20',
                                     command=self.save_image)
        self.save_button.grid(row=20,column=0,columnspan=4,sticky='ew')


    def populate_params(self):
        self.trim_widgets()
        self.resize_widgets()
        self.add_crement_buttons()
        self.grid_checkbox()    
        self.grid_textbox()
        self.flip_checkbox()
        self.grayscale_box()
        self.add_save_button()
    
    #add browsing textbox to frame_buttons
    def im_to_display(self):
        self.path_to_im = tk.Entry(self.frame_buttons, width=35, borderwidth=2, 
                                   bg='black', fg='lime green', font='Arial 20')
        self.path_to_im.insert(0,'path/to/image.png')
        self.path_to_im.grid(row=0,column=0,columnspan=2)
        self.add_browse_button()
        self.add_enter_button()

    #add browse button to frame_buttons
    def add_browse_button(self):
        self.button_explore = tk.Button(self.frame_buttons ,text="Browse", padx=10, pady=5, 
                                        font='Arial 18', command=self.browseFiles)
        self.button_explore.grid(row=1,column=0)

    #add enter/refresh button to frame_buttons
    def add_enter_button(self):
        self.path_button = tk.Button(self.frame_buttons, text='Enter/Refresh', padx=10, pady=5, 
                                 font='Arial 18', command=self.initiate_canvas)
        self.path_button.grid(row=1,column=1)

    #function for opening the file explorer window
    def browseFiles(self):
        filename = filedialog.askopenfilename(initialdir = self.initial_browsedir, 
                                              title = "Select a File", 
                                              filetypes = ([('Image Files', '.jpg .png .jpeg')]))
        self.path_to_im.delete(0,tk.END)
        self.path_to_im.insert(0,filename)  

    def init_display_size(self):
        #aim --> match display frame size with that once the canvas is added
        #the idea is for consistent aestheticsTM
        self.fig = figure.Figure(figsize=(6,6), layout="constrained")
        #self.fig.subplots_adjust(left=0.06, right=0.94, top=0.94, bottom=0.06)

        self.ax = self.fig.add_subplot()
        self.im = self.ax.imshow(np.zeros(100).reshape(10,10),origin='lower')
        self.ax.set_title('Click "Browse" to the right to begin!',fontsize=15)
        self.text = self.ax.text(x=2.8,y=5.0,s='Your Image',color='red',fontsize=28)
        self.text = self.ax.text(x=2.9,y=4.1,s='Goes Here',color='red',fontsize=28)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_display) 

        #add canvas 'frame'
        self.label = self.canvas.get_tk_widget()
        self.label.grid(row=0,column=0,columnspan=4,rowspan=6,sticky='nsew')
    
    #setting up file variables
    def img_firstpass(self):
        full_filepath = str(self.path_to_im.get())

        self.img_only = Image.open(full_filepath).convert('RGB')
        self.img_array = np.asarray(self.img_only)

        #add title...because why not?
        try:
            full_filepath = full_filepath.split('/')   #split full pathname into components
            full_filename = full_filepath[-1]          #isolate filename
            split_filename = full_filename.split('.')  #separate image name from file extension
            self.filename = split_filename[0]
        except:
            print('Error. Defaulting to "Generic" for canvas title.')
            self.filename = 'Generic'
        
    def draw_im_canvas(self):

        #delete any and all miscellany from the canvas (including that which was created
        #using self.init_display_size())
        self.label.delete('all')
        self.ax.remove()

        #reset checkboxes
        self.gridcheck.deselect()
        self.flipcheck.deselect()
        self.graycheck.deselect()
        
        self.ax = self.fig.add_subplot()
        self.im = self.ax.imshow(np.flipud(self.img_array),origin='lower',cmap='gray')

        self.ax.set_title(f'{self.filename}',fontsize=15)
        
        self.create_axislabels()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_display)    

        #add canvas 'frame'
        self.label = self.canvas.get_tk_widget()
        self.label.grid(row=0,column=0,columnspan=3,rowspan=6)
    
    #use ONLY for the enter/refresh button. first file pass!
    def initiate_canvas(self):
        self.img_firstpass()
        self.draw_im_canvas()
    
    #this function helps ensure that pixel cells are square- and not rectangular-shaped
    def get_scaling_fraction(self):
        
        self.height = np.shape(self.img_array)[0]
        self.width = np.shape(self.img_array)[1]
        
        if (self.height>self.width) & ((self.width/self.height)<0.99):
            fraction = self.width/self.height
            return 1, fraction
        elif (self.height<self.width) & ((self.height/self.width)<0.99):
            fraction = self.height/self.width
            return fraction, 1
        elif (self.height==self.width) | ((self.width/self.height)>0.99) | ((self.height/self.width)>0.99):
            return 1, 1
        else:
            print("I don't know what to tell ye. Your width and/or height are not numbers.")
            return None

    def im_trim(self):        #...thank you, chatgpt.
        
        try:
            #reshape image array to (number of pixels, number of channels)
            pixels = self.img_array.reshape(-1, self.img_array.shape[2])
            
            #find most common color -- ASSUMED to be background color!
            unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
            background_color = unique_colors[counts.argmax()]
            
            #create new image with background color (I *think* it only contains that background color)
            bg = Image.new(self.img_only.mode, self.img_only.size, tuple(background_color))
        
        #if any steps beget errors, then claim the background color is the color of the upper left px
        except:
            bg = Image.new(self.img_only.mode, self.img_only.size, self.img_only.getpixel((0,0)))
            
        #subtract background from image
        diff = ImageChops.difference(self.img_only, bg)
        
        #convert difference to grayscale...I guess.
        diff = diff.convert('L')
        
        #threshold difference image to create a binary image
        #pixel values > threshold set to white (255), pixels < threshold set to black (0)
        threshold = float(self.threshold_val.get())
        
        diff = diff.point(lambda p: p > threshold and 255)
        
        #get bounding box of non-background region
        bbox = diff.getbbox()
        
        if bbox:
            self.img_only = self.img_only.crop(bbox)
            self.img_array = np.asarray(self.img_only)
        else:
            print("No content found to trim - retaining original image dimension.")
                
    def im_trim_preview(self):
        
        self.im_trim()
        self.draw_im_canvas()
    
    #resizing the image and recreating the canvas.
    def resize_im(self):
        self.img_firstpass()
        
        if self.trimvar.get():
            self.im_trim()

        self.frac_h, self.frac_w = self.get_scaling_fraction() 
        self.npixels = int(self.npx.get())
        
        #resize "smoothly" down to desired number of pixels for x (nx*frac_w) and y (nx*frac_h)
        #resample options: NEAREST, BILINEAR, BICUBIX, LANCZOS, BOX, HAMMING
        self.img_only = self.img_only.resize((int(self.npixels*self.frac_w), 
                                                int(self.npixels*self.frac_h)),
                                               resample=Image.NEAREST)
        
        
        try:
            #I assume users who select ncolor=2 are wanting a black/white BINARY image! 
            if int(self.ncolor.get())==2:
                self.img_only = self.img_only.convert('L')
                
                #the otsu threshold helps to automate the process of selecting which pixels are assigned 
                #to white, and which to black.
                otsu_threshold = threshold_otsu(np.asarray(self.img_only))
                
                #assign black if x>threshold and 0 if x<threshold, where x is the pixel value
                self.img_only = self.img_only.point(lambda x: 255 if x>otsu_threshold else 0,mode='1')
            else:
                #otherwise, proceed as normal. :-)
                ncol = int(self.ncolor.get())
                self.img_only = self.img_only.quantize(colors=ncol,method=1,kmeans=ncol)
                self.img_only = self.img_only.convert('RGB')
                
        except:
            self.img_only = self.img_only
        
        self.img_array = np.asarray(self.img_only)
        self.draw_im_canvas()
    
    def flip_xaxis(self):
        
        self.create_axislabels()
        offset = float(self.offset_val.get())
        
        if self.flipvar.get():
            self.ax.set_xlim(np.shape(self.img_array)[1]-offset,0)
        else:
            self.ax.set_xlim(0,np.shape(self.img_array)[1]-offset)
        
        self.ax.tick_params(labelsize=12)
        self.ax.set_xticks(self.xticks,labels=self.xlabels,fontsize=12)
        self.ax.set_yticks(self.yticks,labels=self.ylabels,fontsize=12)
        self.canvas.draw()
    
    def convert_grayscale(self):
        
        if self.grayvar.get():
            self.im.remove()
            
            img_only_gray = self.img_only.convert('L')
            img_array_gray = np.asarray(img_only_gray)
            
            self.im = self.ax.imshow(np.flipud(img_array_gray),origin='lower',cmap='gray')
            self.canvas.draw()
        else:
            self.im.remove()
            self.im = self.ax.imshow(np.flipud(self.img_array),origin='lower')
            self.canvas.draw()
    
    def create_axislabels(self):
        
        line_spacing = int(self.line_spacing.get())
        offset = float(self.offset_val.get())
        
        self.xticks = []
        self.yticks = []
        self.xlabels = []
        self.ylabels = []
        
        #the lim will help prevent tick label crowding for LARGE images. :-)
        lim = 10 if ((np.shape(self.img_array)[0]<250)&(np.shape(self.img_array)[1]<250)) else 150
        
        #set up y ticks and y labels
        for n in range(0,np.shape(self.img_array)[0],line_spacing):
            #for labels --> only include 0s and multiples of 10.
            if n==0:
                self.yticks.append(n-offset)
                self.ylabels.append(n)
            if (n+1)%int(lim)==0:
                self.yticks.append(n+offset)
                self.ylabels.append(n+1)
        
        #set up x ticks and x labels
        for n in range(0,np.shape(self.img_array)[1],line_spacing):
            #for labels --> only include 0s and multiples of 10.
            if n==0:
                self.xticks.append(n-offset)
                self.xlabels.append(n)
            if (n+1)%int(lim)==0:
                self.xticks.append(n+offset)
                self.xlabels.append(n+1)
            
        self.ax.tick_params(labelsize=12)
        self.ax.set_xticks(self.xticks,labels=self.xlabels,fontsize=12)
        self.ax.set_yticks(self.yticks,labels=self.ylabels,fontsize=12)
                    
    
    def add_grid(self):
        
        if self.var.get()==1:
            
            self.create_axislabels()
            
            user_color = self.color_grid.get()
            line_spacing = int(self.line_spacing.get())
            offset = float(self.offset_val.get())
            line_thickness = float(self.line_thickness.get())
            
            self.xlines = []
            self.ylines = []
    
            #set y gridlines
            for n in range(0,np.shape(self.img_array)[0],line_spacing):
                line = self.ax.axhline(n+offset,lw=line_thickness,color=user_color,alpha=0.6)
                self.xlines.append(line)

            #set x gridlines
            for n in range(0,np.shape(self.img_array)[1],line_spacing):
                line = self.ax.axvline(n+offset,lw=line_thickness,color=user_color,alpha=0.6)
                self.ylines.append(line)    
                    
            self.ax.tick_params(labelsize=15)
            self.ax.set_xticks(self.xticks,labels=self.xlabels,fontsize=15)
            self.ax.set_yticks(self.yticks,labels=self.ylabels,fontsize=15)
            
            self.canvas.draw()
                
        else:
            for n in self.xlines:
                n.remove()
                #self.ax.xaxis.set_major_locator(ticker.AutoLocator())
            for n in self.ylines:
                n.remove()
                #self.ax.yaxis.set_major_locator(ticker.AutoLocator())
            self.canvas.draw()
            
if __name__ == "__main__":
    
    #unpack params.txt file here
    if '-h' in sys.argv or '--help' in sys.argv:
        print("USAGE: %s [-params (name of parameter.txt file, no single or double quotations marks)]")
    
    if '-params' in sys.argv:
        p = sys.argv.index('-params')
        param_file = str(sys.argv[p+1])
        
    #create dictionary with keyword and values from param textfile
    param_dict={}
    with open(param_file) as f:
        for line in f:
            try:
                key = line.split()[0]
                val = line.split()[1]
                param_dict[key] = val
            except:
                continue
        
        #extract parameters and assign to variables...
        path_to_repos = param_dict['path_to_repos']
        initial_browsedir = param_dict['initial_browsedir']
        save_path = param_dict['save_path']
        window_geometry = param_dict['window_geometry']
        init_offset = param_dict['init_offset']
        
        app = App(path_to_repos, initial_browsedir, save_path, window_geometry, init_offset)
        app.mainloop()
        