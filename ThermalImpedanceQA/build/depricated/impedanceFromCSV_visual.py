import numpy as np
import os
import csv
import logging
import argparse
import configparser
from matplotlib import pyplot as plt
from stave import Stave
from analyze import readFile, getVars

import pandas as pd
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk

global fileList
global dirmemory

fileList = []
dirmemory = "/"

def browseFiles():
    global fileList
    global dirmemory

    #list of files
    fileList = filedialog.askopenfilenames(initialdir = dirmemory, title = "Select a File", filetypes = (("numpy.savez","*.npz*"),("all files","*.*")))

    #use the name of the first file in the list to find the containing folder for all files in fileList
    if len(fileList) > 0:
        file = fileList[0]
        print(file)
        filerev = file[::-1]
        filerev = filerev[filerev.find("/"):len(filerev)]
        dirmemory = filerev[::-1]

    #notification of action
    print("File explorer is open at location: " + dirmemory)
    label_file_explorer.configure(text= str(len(fileList)) + " Files Opened at: " + dirmemory)
    directory.set(dirmemory)


def analyze():
    for i in fileList:
        analyzeFile(i)

def orient():
    oneFace = singleFace.get()
    manual = manualBoundaries
    l_bounds = [i.get() for i in left_boundaries]
    r_bounds = [i.get() for i in right_boundaries]
    bounds = l_bounds + r_bounds
    orient = orientation.get()
    l_boundsFull = any(not elem == "0" for elem in l_bounds)
    r_boundsFull = any(not elem == "0" for elem in r_bounds)
    bothBounds = l_boundsFull or r_boundsFull
    noBounds = not l_boundsFull and not r_boundsFull

    if manual and noBounds:
        label_file_explorer.configure(
            text="Error: please enter manual bounds or deselect the 'manual boundaries' option.")
        return

    if oneFace and bothBounds:
        label_file_explorer.configure(
            text="Error: please delete extra bounds from the face not being analyzed.")
        return
    
def analyzeFile(inputFile):
    config = configparser.ConfigParser()

    image, config['Default'] = readFile(inputFile)
    if image == None:
        print('Need to load a csv or npy file.')
        label_file_explorer.configure('Please ensure every file selected is in .csv, .npy, or .npz file formats.')
        return
    
    getVars()

def getVars(nTrim, adc, emissivity):
    config = configparser.ConfigParser

    print("Taking values from config variables given by user input.")

    if not len(nTrim) == 0:
        print("Overriding nTrim value!")
        config['Default']['nTrim'] = nTrim

    if "c_liquid" not in config["Default"]:
        config["Default"]["c_liquid"] = config["Default"]["c_liquid_hot"] if config["Default"]["regime"] == "hot" else config["Default"]["c_liquid_cold"]

    if "liquid_density" not in config["Default"]:
        config["Default"]["liquid_density"] = config["Default"]["liquid_density_hot"] if config["Default"]["regime"] == "hot" else config["Default"]["liquid_density_cold"]

    if adc:
        from process_tc_data import adc_to_temp, DEFAULT_PARAMETERS 
        params = DEFAULT_PARAMETERS.copy()

    if not emissivity == 0.92:
        params['Emissivity'] = emissivity
        image = adc_to_temp(image, params)
        print('average temp') 
        print(np.mean(image))


root = Tk()
#getting screen width and height of display
width= root.winfo_screenwidth() 
height= root.winfo_screenheight()
#setting tkinter window size
root.geometry("%dx%d" % (width, height))

for i in range(5):
    root.columnconfigure(i, weight=1)
for j in range(10):
    root.rowconfigure(j, weight=1)

orientation = IntVar(value=0)
singleFace = BooleanVar(value=False)
emissivity = IntVar(value=0.92)
killEmissivity = BooleanVar(value=True)
debug = BooleanVar(value=False)
directory = StringVar(value=dirmemory)
manualBoundaries = BooleanVar(value=False)
ntrim = StringVar(value='')
adc = BooleanVar(value=True)

#ask Jesse how this is supposed to work
left_boundaries = []
right_boundaries = []
for i in range(4):
    var_l = StringVar(value="0") 
    var_r = StringVar(value="0") 
    left_boundaries.append(var_l)
    right_boundaries.append(var_r)


label_file_explorer = Label(root, height=1, width = 100, text="Batch Calculate Impedance for Thermal QC.", foreground="blue")

controls_frame=LabelFrame(root, text="Controls")
button_explore = Button(controls_frame, text = "Browse Files", command = browseFiles, width=10, height=1, cursor= "hand2")
label_outpath = Label(controls_frame, text="Files writing to:", width=20, height=1)
textbox_outpath = Entry(controls_frame, textvariable = directory, width=20)
button_debug = Checkbutton(controls_frame, text="Run in debug mode", var=debug, width=20, height=1)
button_exit = Button(controls_frame, text = "Exit", command = exit, width=10, height=1, cursor= "hand2")

orientation_frame = LabelFrame(root, text="Orientation")
button_orientation_L = Radiobutton(orientation_frame, text="L-side", value=1, var=orientation, width=10, height=1)
button_orientation_J = Radiobutton(orientation_frame, text="J-side", value=2, var=orientation, width=10, height=1)
button_orientation_K = Radiobutton(orientation_frame, text="K-side", value=3, var=orientation, width=10, height=1)
button_singleFace = Checkbutton(orientation_frame, text="Single face?", var=singleFace, width=20, height=1)
button_confirmOrientation = Button(orientation_frame, text="Confirm", command = orient, width=10, height=1)

borders_frame=LabelFrame(root, text="Boundaries", width=1000, height=1200)
button_manual_boundaries = Checkbutton(borders_frame, text="use manual boundaries", width=20, height=1, var=manualBoundaries)
LeftSide_left = Entry(borders_frame, textvariable=left_boundaries[0], width=4)
LeftSide_top = Entry(borders_frame, textvariable=left_boundaries[2], width=4)
LeftSide_right = Entry(borders_frame, textvariable=left_boundaries[1], width=4)
LeftSide_bottom = Entry(borders_frame, textvariable=left_boundaries[3], width=4)

trim_frame = Frame(borders_frame)
n_trim = Entry(trim_frame, textvariable = ntrim, width=4)
trim_label = Label(trim_frame, text = "nTrim parameter", width=20, height=1)
trim_label.pack(side=LEFT)
n_trim.pack(side=LEFT)

RightSide_left = Entry(borders_frame, textvariable=right_boundaries[0], width=4)
RightSide_top = Entry(borders_frame, textvariable=right_boundaries[2], width=4)
RightSide_right = Entry(borders_frame, textvariable=right_boundaries[1], width=4)
RightSide_bottom = Entry(borders_frame, textvariable=right_boundaries[3], width=4)

pictures = [ImageTk.PhotoImage(Image.open('ThermalImpedanceQA\\PXL_20240628_200320287.jpg').resize([80,160])), 
            ImageTk.PhotoImage(Image.open('ThermalImpedanceQA\\PXL_20240628_200312264.jpg').resize([80,160])), 
            ImageTk.PhotoImage(Image.open('ThermalImpedanceQA\\green-screen-explosion.gif').resize([80,160]))]

RightSide_label = Label(borders_frame, image= pictures[1], width=100, height=175)
LeftSide_label = Label(borders_frame, image= pictures[0], width=100, height=175)

weights = [2,2,2,1,2,2,2]
for i in range(7):
    borders_frame.columnconfigure(i)
for j in range(7):
    borders_frame.rowconfigure(j)

emissivity_frame = LabelFrame(root, text="Emissivity")
button_normalize = Checkbutton(emissivity_frame, text="Normalize shininess", var = killEmissivity, width=20, height=1)
textbox_emissivity = Entry(emissivity_frame, textvariable = emissivity, width=20)
button_adc = Checkbutton(emissivity_frame, text="ADC variables", var = adc, width=20, height=1)

analyze_button = Button(root, text="Analyze!", width=20, height=10, command=analyze, bg="dark green", fg="light grey")

label_file_explorer.grid(column=1, columnspan=5, row=1, sticky=W)

controls_frame.grid(column=1, row=2, sticky=N)
button_explore.pack(side=TOP, pady=[10,0])
label_outpath.pack(side=TOP)
textbox_outpath.pack(side=TOP, pady=3)
button_debug.pack(side=TOP)
button_exit.pack(side=TOP, pady=[0,10])

orientation_frame.grid(column=2, row=2, sticky=N)
button_orientation_L.pack(side=TOP, pady=[10,0])
button_orientation_J.pack(side=TOP)
button_orientation_K.pack(side=TOP)
button_singleFace.pack(side=TOP)
button_confirmOrientation.pack(side=TOP, pady=[0,10])

emissivity_frame.grid(column=2, row=3, sticky=N)
button_normalize.pack(side=TOP, pady=[10,0])
textbox_emissivity.pack(side=TOP)
button_adc.pack(side=TOP, pady=[0,10])

borders_frame.grid(column=3, row=2, columnspan=4, rowspan=5, sticky=NW)
button_manual_boundaries.grid(column=3, row=0, columnspan=3)
LeftSide_label.grid(column=1, row=3, rowspan=4)
RightSide_label.grid(column=6, row=3, rowspan=4)

LeftSide_left.grid(column=0, row=4, padx=[10,0], sticky=SE)
LeftSide_right.grid(column=2, row=4, sticky=SW)
LeftSide_top.grid(column=1, row=2)
LeftSide_bottom.grid(column=1, row=8, pady=[0,10])
RightSide_left.grid(column=5, row=4, sticky=SE)
RightSide_right.grid(column=7, row=4, padx=[0,10], sticky=SW)
RightSide_top.grid(column=6, row=2)
RightSide_bottom.grid(column=6, row=8, pady=[0,10])
trim_frame.grid(column=3, row=8)

analyze_button.grid(column=2, row=5, sticky=N)

LeftSide_label.update()
RightSide_label.update()
root.mainloop()