import numpy as np
import os
import csv
import logging
import argparse
import configparser
from matplotlib import pyplot as plt
from stave import Stave

def readFile(inputFile, emissivity):
    match inputFile[-3:]:
        case 'csv':
            print("Opening CSV file.")
            image = []
            with open(inputFile) as csvfile:
                reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                for row in reader:
                    image.append(row)
            image = np.array(image)
        
        case 'npy':
            print("Loading NPY data.")
            image = np.load(inputFile)
        
        case 'npz':
            print("Mucking about with NPZ file. ")
            npzfile = np.load(inputFile, allow_pickle=True)
            from process_tc_data import npz_images_to_temp
            image = npz_images_to_temp(npzfile['image'], emissivity=emissivity)

            temp_in = np.median(npzfile['thermo_data'][-5:,2])
            config = {
                'temp_in': temp_in,
                'temp_out': np.median(npzfile['thermo_data'][-5:,3]),
                'flow_rate': np.median(npzfile['flow_data'][-5:]),
                'regime': 'cold' if temp_in < 0 else 'hot',
                }
        case _:
            return None, None
        
    return image, config

def getVars(image, nTrim, adc, emissivity):
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

def getBounds(manual_boundaries, one_face, orientation, r_bounds = [], l_bounds = []):
    config = configparser.ConfigParser

    print("getting bounds from user inputs")

    #see original file for more detailed history of the following two chunks of code

    #####trying two below
    #if args.orientation == 'L':
    image = np.flip(image, axis=1)
    #image = np.flip(image, axis=0)

    ######March 11 this is good for new cam. need to figure out L orientation 
    if orientation == 2: #if J-side
        image = np.flip(image, axis=0)
        image = np.flip(image,axis=1)

    #creating the staves + loading the parameters from the config file
    #scale up the images with linear extrapolation to get better results for small regions
    staveTop = Stave(image, config)
    staveTop.ScaleImage(10)
    if orientation == 0:
        staveBottom = Stave(image, config)
        staveBottom.ScaleImage(10)

    if manual_boundaries:
        
        r_boundsFull = any(not i == "0" for i in r_bounds)
        l_boundsFull = any(not i == "0" for i in l_bounds)
        # if the manual boundaries are set - use them
        if not l_boundsFull and not r_boundsFull:
            print("Please provide one set of boundaries for one-face measurement.")
            return
        elif one_face and r_boundsFull and l_boundsFull:
            print("Too many bounds! please provide one set of boundaries for one-face measurements.")
            return
        elif one_face and r_boundsFull:
            bounds = [float(i) for i in r_bounds]
            staveTop.DefineStave(bounds)
        elif one_face and l_boundsFull:
            bounds = [float(i) for i in l_bounds]
            staveTop.DefineStave(bounds)
        
        #Above is the original original code before we modified it for Yale's default 1 face
        #Jesse changed below on Feb 20 to fix the manual boundary problem. 
        #if args.orientation is None:
            #staveTop.DefineStave(args.manual_boundaries[:4])


        elif not one_face:
            if not l_boundsFull or not r_boundsFull:
                print("You have only provided 4 boundaries, while 8 are expected.")
                print("Please provide 8 boundaries or run with the -1f option. Exiting...")
                quit()
            top_bounds = [float(i) for i in l_bounds]
            bottom_bounds = [float(i) for i in r_bounds]
            staveTop.DefineStave(top_bounds)
            staveBottom.DefineStave(bottom_bounds)
        print("Stave edges were manually set to: ")
    else:
        #finding the staves - triggers an algorithm that looks for the stave, using relative coordinates
        if orientation == 0:
            staveTop.FindStaveWithin(0,1.0,0,0.46)
            staveBottom.FindStaveWithin(0,1.0,0.54,1.0)
        else:
            staveTop.FindStaveWithin(0,1.0,0,1.0)
        #print the positions of the staves
        print("Staves' edges found at:")

        staveTop.Echo()
        if orientation==0:
            staveBottom.Echo()
