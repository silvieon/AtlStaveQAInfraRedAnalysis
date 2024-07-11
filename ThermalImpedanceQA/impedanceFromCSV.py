#!/usr/bin/env python

'''
impedanceFromCSV.py

Author: Lubos Vozdecky (Queen Mary, University of London)
About: This program takes a thermal image of an ATLAS Itk Stave Support in CSV format,
  finds the stave and computes the thermal impedances using data of the cooling fluid saved in parameters.cfg.
  The program outputs the result impedances into the /data folder as a CSV file.
'''

import numpy as np
import os
import csv
import logging
import argparse
import configparser
from matplotlib import pyplot as plt
from stave import Stave

parser = argparse.ArgumentParser()
parser.add_argument("path", help="The path to the input CSV file")
parser.add_argument("config", help="The path to the configuration file")
parser.add_argument("-o", "--outpath", default="./output", help="Needs a folder for output path")
parser.add_argument("-d","--debug", help="Runs the code in debug mode", action="store_true")
parser.add_argument("-g","--graphs", help="Outputs the graph", action="store_true")
parser.add_argument("-1f","--one_face", help="Using IR image with one face only", action="store_true")
#parser.add_argument("-L","--L_flip", help="Flips the input image horizontally  before processing.", action="store_true")
#parser.add_argument("-J","--J_flip", help="Flips the input image both vertically and horizontally before processing.", action="store_true")
#parser.add_argument("-K", "--K_flip", action="store_true")
parser.add_argument('--orientation', choices=['J', 'L', 'K'], help="Decides which side stave you have")
parser.add_argument('-m','--manual_boundaries', type = int, nargs='+',
                    help="Sets manual boundaries that overwrite the search algorithm. Use 4 (or 8) numbers divided by space. Format: [left,right,top,bottom]")
parser.add_argument('--adc', action = "store_true", help = "Assume input is in adc units")
parser.add_argument('--emissivity', default=0.92, type = float, help = "Overwriting emissivity value in adc_to_temp")
parser.add_argument('--kill-shiny', action="store_true", help = "Getting rid of the bond pad shinyness")
parser.add_argument('--nTrim', type=int, help="nTrim parameter from config file; trims pixels above/below the stave edges")
args = parser.parse_args()


inputFile = args.path
configFile = args.config

#check if the suffix is .csv
#if inputFile[-3:] != "csv":
  #print("The input file should be a .csv file")
  #quit()

#delete the debug folder if it exists and create a new one
if args.debug:
  if not os.path.isdir("debug_output"):
    os.mkdir("debug_output")
  if os.path.isfile("debug_output/debug.log"):
    os.remove("debug_output/debug.log")

#create the output folder if it doesn't exist
#if not "output" in os.listdir("."):
  #os.system("mkdir output")
#os.makedirs(args.outpath, exist_ok=True)


#set up the debugging log
#if args.debug:
 # logging.basicConfig(filename='debug_output/debug.log',level=logging.DEBUG)

#if args.L_flip and args.J_flip:
 # print("Cannot have both L and J flip options activated at the same time. Exiting...")
  #exit()

#get the git version of the code so it can be printed on the output graphs
#gitHash = os.popen('git rev-parse --short HEAD').read()[:-2]
#gitDate = os.popen('git log -1 --format=%cd').read()

#logging.debug("Running the code version: " + gitHash + " " + gitDate)

config = configparser.ConfigParser()

if inputFile[-3:] == 'csv': 
  #fetch the CSV file
  logging.debug("Opening the CSV file")
  imgList = []
  with open(inputFile) as csvfile:
    reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
    for row in reader:
      imgList.append(row)
  image = np.array(imgList) 

elif inputFile[-3:] == 'npy':
  image = np.load(inputFile)
elif inputFile[-3:] == 'npz':
  assert not args.adc
  npzfile = np.load(inputFile, allow_pickle=True)
  from process_tc_data import npz_images_to_temp
  image = npz_images_to_temp(npzfile['image'], emissivity=args.emissivity)
  # note: only use the last 5 data points for averaging
  temp_in = np.median(npzfile['thermo_data'][-5:,2])
  logging.debug('Loading process variables from npz data')
  config['Default'] = {
    'temp_in': temp_in,
    'temp_out': np.median(npzfile['thermo_data'][-5:,3]),
    'flow_rate': np.median(npzfile['flow_data'][-5:]),
    'regime': 'cold' if temp_in < 0 else 'hot',
  }

else:
  print('Need to load a csv or npy file')
  quit()

logging.debug("Importing variables from config file " + configFile + " in the impedanceFromCSV.py script.")
config.read(args.config)
# override ntrim if provided
if args.nTrim is not None:
  print("Overriding nTrim value!")
  config['Default']['nTrim'] = args.nTrim

if "c_liquid" not in config["Default"]:
  config["Default"]["c_liquid"] = config["Default"]["c_liquid_hot"] if config["Default"]["regime"] == "hot" else config["Default"]["c_liquid_cold"]

if "liquid_density" not in config["Default"]:
  config["Default"]["liquid_density"] = config["Default"]["liquid_density_hot"] if config["Default"]["regime"] == "hot" else config["Default"]["liquid_density_cold"]

if args.adc:
  from process_tc_data import adc_to_temp, DEFAULT_PARAMETERS 
  params = DEFAULT_PARAMETERS.copy()

  if args.emissivity is not None:
    params['Emissivity'] = args.emissivity
  image = adc_to_temp(image, params)
  print('average temp') 
  print(np.mean(image))

#Jesse switched J and L on Jan 19
  #J switched back to "correct" on march 8
#if args.orientation == 'L':
  #image = np.flip(image, axis=1)
  #image = np.flip(image, axis=0)


#if args.orientation == 'J':
  #image = np.flip(image,axis=1)

#if args.orientation == 'K':
  #image = np.flip(image,axis=0)


#####trying two below
#if args.orientation == 'L':
  image = np.flip(image, axis=1)
  #image = np.flip(image, axis=0)

######March 11 this is good for new cam. need to figure out L orientation 
if args.orientation == 'J':
  image = np.flip(image, axis=0)
  image = np.flip(image,axis=1)




###Way back original flips
#if args.J_flip:
 # image = np.flip(image,axis=0)
  #image = np.flip(image,axis=1)

#if args.K_flip:
 # image = np.flip(image,axis=0)


#creating the staves + loading the parameters from the config file
staveTop = Stave(image, config)
if args.orientation is None:
  staveBottom = Stave(image, config)

#scale up the images with linear extrapolation to get better results for small regions
staveTop.ScaleImage(10)
if args.orientation is None:
  staveBottom.ScaleImage(10)


if args.manual_boundaries:
  # if the manual boundaries are set - use them
  if args.one_face:
    staveTop.DefineStave(args.manual_boundaries[:4])
  #Above is the original original code before we modified it for Yale's default 1 face
  #Jesse changed below on Feb 20 to fix the manual boundary problem. 
  #if args.orientation is None:
    #staveTop.DefineStave(args.manual_boundaries[:4])
  else:
    if len(args.manual_boundaries) < 8:
      print("You have only provided 4 boundaries, while 8 are expected.")
      print("Please provide 8 boundaries or run with the -1f option. Exiting...")
      quit()
    staveTop.DefineStave(args.manual_boundaries[:4])
    staveBottom.DefineStave(args.manual_boundaries[4:])
  print("Stave edges were manually set to:")
else:
  #finding the staves - triggers an algorithm that looks for the stave, using relative coordinates
  if args.orientation is None:
    staveTop.FindStaveWithin(0,1.0,0,0.46)
    staveBottom.FindStaveWithin(0,1.0,0.54,1.0)
  else:
    staveTop.FindStaveWithin(0,1.0,0,1.0)
  #print the positions of the staves
  print("Staves' edges found at:")

staveTop.Echo()
if args.orientation is None:
  staveBottom.Echo()


#create a deep copy of the image, to which the edges/regions will be drawn
#staveTop.DrawEdges(img_edges)
#if args.orientation is None:
  #staveBottom.DrawEdges(img_edges)

if args.kill_shiny:
  staveTop.killShiny(bbox=((60,10),(165,50)),dx=412.5)


numModules = 14

#get the scaled image; it's used later for showing the regions for debugging
img_edges = staveTop.getImage()

#large regions
for i in range(numModules):
  staveTop.AddRegion(i*1.0/numModules,(i+1)*1.0/numModules,0.0,0.5,"large")
  if args.orientation is None:
    staveBottom.AddRegion(i*1.0/numModules,(i+1)*1.0/numModules,0.5,1.0,"large")

#large regions - return pipe
for i in reversed(range(numModules)):
  staveTop.AddRegion(i*1.0/numModules,(i+1)*1.0/numModules,0.5,1.0,"large")
  if args.orientation is None:
    staveBottom.AddRegion(i*1.0/numModules,(i+1)*1.0/numModules,0.0,0.5,"large")

#small regions above the pipe
for i in range(numModules):
  #exception for near-edge regions
  if i == 0:
    staveTop.AddRegion(i*1.0/numModules + 0.1/numModules,(i+1)*1.0/numModules,0.247826,0.317391,"small")
    if args.orientation is None:
      staveBottom.AddRegion(i*1.0/numModules + 0.1/numModules,(i+1)*1.0/numModules,0.682609,0.752174,"small")
  elif i==13:
    staveTop.AddUBendRegion(i*1.0/numModules,(i+1)*1.0/numModules - 0.0174545,0.247826,0.317391,0.13,0.0869565,"small",bend="downwards")
    if args.orientation is None:
      staveBottom.AddUBendRegion(i*1.0/numModules,(i+1)*1.0/numModules - 0.0174545,0.682609,0.752174,0.13,0.0869565,"small",bend="upwards")
  else:
    staveTop.AddRegion(i*1.0/numModules,(i+1)*1.0/numModules,0.247826,0.317391,"small")
    if args.orientation is None:
      staveBottom.AddRegion(i*1.0/numModules,(i+1)*1.0/numModules,0.682609,0.752174,"small")
#small regions above the pipe (return pipe)
for i in reversed(range(numModules)):
  #exception for near-edge regions
  if i == 0:
    staveTop.AddRegion(i*1.0/numModules + 0.1/numModules,(i+1)*1.0/numModules,0.682609,0.752174,"small")
    if args.orientation is None:
      staveBottom.AddRegion(i*1.0/numModules + 0.1/numModules,(i+1)*1.0/numModules,0.247826,0.317391,"small")
  elif i==13:
    staveTop.AddUBendRegion(i*1.0/numModules,(i+1)*1.0/numModules - 0.0174545,0.682609,0.752174,0.13,0.0869565,"small",bend="upwards")
    if args.orientation is None:
      staveBottom.AddUBendRegion(i*1.0/numModules,(i+1)*1.0/numModules - 0.0174545,0.247826,0.317391,0.13,0.0869565,"small",bend="downwards")
  else:
    staveTop.AddRegion(i*1.0/numModules,(i+1)*1.0/numModules,0.682609,0.752174,"small")
    if args.orientation is None:
      staveBottom.AddRegion(i*1.0/numModules,(i+1)*1.0/numModules,0.247826,0.317391,"small")

#end-of-stave ear region
#the region is defined to stay safely away from the edges: in x direction 0.1 of module length is subtracted from both sides; for y direction it's 5% of the stave width
staveTop.AddRegion(0.1/numModules,154.0/1375-0.1/numModules,-49.0/115+0.05,0.0,"ear")
if args.orientation is None:
  staveBottom.AddRegion(0.1/numModules,154.0/1375-0.1/numModules,1.0,1.0+49.0/115-0.05,"ear")

#drawing the regions
#staveTop.DrawRegions(img_edges,"large")
#staveTop.DrawRegions(img_edges,"small")
#staveTop.DrawRegions(img_edges,"ear")

staveTopTemp = staveTop.getTemperatures("small")


if args.orientation is None:
  staveBottom.DrawRegions(img_edges,"small")
  staveBottom.DrawRegions(img_edges,"large")
  staveBottom.DrawRegions(img_edges,"ear")

  staveBottomTemp = staveBottom.getTemperatures("small")

#correcting the temperature for the regions around the EoS ear (see Documents/2020-09-09-EOS-Impedances.pdf)
temperatureProfile = [float(x) for x in config["Default"]["temperatureProfile"].split(",")]
#total heat given up by the liquid per second
flowRateKgPerSec = (float(config["Default"]["flow_rate"])/(60*1000))*float(config["Default"]["liquid_density"])
totalHeat = (float(config["Default"]["temp_in"])-float(config["Default"]["temp_out"]))*float(config["Default"]["c_liquid"])*flowRateKgPerSec
earTempTop = staveTop.getTemperatures("ear")[0]
if args.orientation is None:
  earTempBottom = staveBottom.getTemperatures("ear")[0]

fractionHeat_segment0 = (temperatureProfile[1]-temperatureProfile[0])/(temperatureProfile[-1] - temperatureProfile[0])
fractionHeat_segment1 = (temperatureProfile[2]-temperatureProfile[1])/(temperatureProfile[-1] - temperatureProfile[0])
fractionHeat_segment2 = (temperatureProfile[3]-temperatureProfile[2])/(temperatureProfile[-1] - temperatureProfile[0])

logging.debug("fractionHeat_segment0 = {}".format(fractionHeat_segment0))
logging.debug("fractionHeat_segment1 = {}".format(fractionHeat_segment1))
logging.debug("fractionHeat_segment2 = {}".format(fractionHeat_segment2))

earHeat = (fractionHeat_segment0+fractionHeat_segment1 - 2*fractionHeat_segment2)*totalHeat/2
heatNextEar = (1.0 + 54.0/98)*fractionHeat_segment2*totalHeat/2
#liquid temperature between segments 0 and 1
liqTempAfterSeg0 = float(config["Default"]["temp_in"]) - temperatureProfile[1]*(float(config["Default"]["temp_in"])-float(config["Default"]["temp_out"]))

logging.debug("totalHeat = {}".format(totalHeat))
logging.debug("earTempTop = {}".format(earTempTop))
if args.orientation is None:
  logging.debug("earTempBottom = {}".format(earTempBottom))
logging.debug("earHeat = {}".format(earHeat))
logging.debug("heatNextEar = {}".format(heatNextEar))
logging.debug("liqTempAfterSeg0 = {}".format(liqTempAfterSeg0))

#dT/dQ_region_segment as described in Documents/2020-09-09-EOS-Impedances.pdf
#importing the values from the config file
logging.debug("Loading the correction factors from the config file:")
dTdQ_large_0 = float(config["Default"]["dTdQ_large_0"]) #1.193
dTdQ_large_1 = float(config["Default"]["dTdQ_large_1"]) #0.716
dTdQ_small_0 = float(config["Default"]["dTdQ_small_0"]) #0.591
dTdQ_small_1 = float(config["Default"]["dTdQ_small_1"]) #0.251
dTdQ_nextEar = float(config["Default"]["dTdQ_nextEar"]) #1.152

logging.debug("dTdQ_large_0 = {}".format(dTdQ_large_0))
logging.debug("dTdQ_large_1 = {}".format(dTdQ_large_1))
logging.debug("dTdQ_small_0 = {}".format(dTdQ_small_0))
logging.debug("dTdQ_small_1 = {}".format(dTdQ_small_1))
logging.debug("dTdQ_nextEar = {}".format(dTdQ_nextEar))

#correcting the surface temperatures of the segments around the EoS region
staveTop.setTemperatureCorrection("large",0, earHeat*dTdQ_large_0)
staveTop.setTemperatureCorrection("large",1, earHeat*dTdQ_large_1)
staveTop.setTemperatureCorrection("small",0, earHeat*dTdQ_small_0)
staveTop.setTemperatureCorrection("small",1, earHeat*dTdQ_small_1)
if args.orientation is None:
  staveBottom.setTemperatureCorrection("large",0, earHeat*dTdQ_large_0)
  staveBottom.setTemperatureCorrection("large",1, earHeat*dTdQ_large_1)
  staveBottom.setTemperatureCorrection("small",0, earHeat*dTdQ_small_0)
  staveBottom.setTemperatureCorrection("small",1, earHeat*dTdQ_small_1)

logging.debug("Temperature corrections for staveTop small regions: {}".format(str(staveTop.getTemperatureCorrections("small"))))
logging.debug("Temperature corrections for staveTop large regions: {}".format(str(staveTop.getTemperatureCorrections("large"))))
if args.orientation is None:
  logging.debug("Temperature corrections for staveBottom small regions: {}".format(str(staveBottom.getTemperatureCorrections("small"))))
  logging.debug("Temperature corrections for staveBottom large regions: {}".format(str(staveBottom.getTemperatureCorrections("large"))))

#computing the impedance for the ear
earImpedanceTop = (liqTempAfterSeg0 - earTempTop - heatNextEar*dTdQ_nextEar)/earHeat
print("Z_earTop = {}".format(earImpedanceTop))

if args.orientation is None:
  earImpedanceBottom = (liqTempAfterSeg0 - earTempBottom - heatNextEar*dTdQ_nextEar)/earHeat
  print("Z_earBottom = {}".format(earImpedanceBottom))

#WIP: print the impedance on the plot as well

#extracting the impedances
largeTop = staveTop.getImpedances("large", heatCorrection=True)
smallTop = staveTop.getImpedances("small")

if args.orientation is None:
  largeBottom = staveBottom.getImpedances("large", heatCorrection=True)
  smallBottom = staveBottom.getImpedances("small")

#compute the combined impedance
smallTopThere = np.array(smallTop[0:14])
smallTopReturn = np.array(smallTop[14:28])
impedanceCombinedTop = 1/(1/smallTopThere + 1/np.flip(smallTopReturn))

if args.orientation is None:
  smallBottomThere = np.array(smallBottom[0:14])
  smallBottomReturn = np.array(smallBottom[14:28])
  impedanceCombinedBottom = 1/(1/smallBottomThere + 1/np.flip(smallBottomReturn))

#savign data into the CSV file
outputFilename = os.path.join(args.outpath, inputFile.split("/")[-1][:-4] + "_IMPEDANCES")
print("Outputing data into a file: " + outputFilename + ".csv")
with open(outputFilename+ ".csv", "w+") as f:
  if args.orientation is not None:
    f.write('#, topLargeRegion, topSmallRegion, smallRegionCombinedTop \n')
  else:
    f.write("#, topLargeRegion, bottomLargeRegion, topSmallRegion, bottomSmallRegion, smallRegionCombinedTop, smallRegionCombinedBottom \n")
  for i in range(0,28):
    if i<14:
      if args.orientation is not None:
        f.write(str(i)+", "+str(largeTop[i])+", "+str(smallTop[i])+", "+str(impedanceCombinedTop[i]) + "\n")
      else:
        f.write(str(i)+", "+str(largeTop[i])+", "+str(largeBottom[i])+", "+str(smallTop[i])+", "+str(smallBottom[i]) + ", "+str(impedanceCombinedTop[i]) + ", "+str(impedanceCombinedBottom[i]) + "\n")
    else:
      if args.orientation is not None:
        f.write(str(i)+", "+str(largeTop[i])+", "+str(smallTop[i])+"\n")
      else:
        f.write(str(i)+", "+str(largeTop[i])+", "+str(largeBottom[i])+", "+str(smallTop[i])+", "+str(smallBottom[i]) + "\n")
  f.write("\n")
  f.write("Z_earTop, {} \n".format(earImpedanceTop))
  if args.orientation is None:
    f.write("Z_earBottom, {}".format(earImpedanceBottom))
  f.close()

to_save = {'largeTop':largeTop, 'smallTop':smallTop, 'impedanceCombinedTop':impedanceCombinedTop, 'earImpedanceTop':earImpedanceTop}
if args.orientation is None:
  to_save.update({'largeBottom':largeBottom, 'smallBottom':smallBottom, 'impedanceCombinedBottom':impedanceCombinedBottom, 'earImpedanceBottom':earImpedanceBottom})
np.savez(outputFilename+".npz", **to_save)

#plotting if -g option selected
if args.graphs:
  plt.figure(figsize=(12,6))
  plt.plot(largeTop, label="Large Region: top")
  plt.plot(smallTop, label="Small Region: top")
  plt.plot(impedanceCombinedTop, label="Small Region: top combined")

  if args.orientation is None:
    plt.plot(largeBottom, label="Large Region: bottom")
    plt.plot(smallBottom, label="Small Region: bottom")
    plt.plot(impedanceCombinedBottom, label="Small Region: bottom combined")
    
  plt.plot([-1],[earImpedanceTop],marker='o', linestyle='', label="Z_earTop")
  if args.orientation is None:
    plt.plot([-1],[earImpedanceBottom],marker='o', linestyle='', label="Z_earBottom")
  
  plt.xlabel("Region number")
  plt.ylabel("Thermal Impedance [K/W]")
  plt.title(outputFilename.split("/")[-1])
  if args.orientation is not None:
    yrange = int(1+1.1*np.max([np.max(largeTop),np.max(smallTop),earImpedanceTop]))
  else:
    yrange = int(1+1.1*np.max([np.max(largeTop),np.max(largeBottom),np.max(smallTop),np.max(smallBottom),earImpedanceTop,earImpedanceBottom]))
  plt.xticks(np.arange(0, 28, 1.0))
  plt.yticks(np.arange(0, yrange, 0.5))
  plt.axis([-2.0,27.5,0,yrange])
  plt.grid()
  plt.legend(ncol=3)
  #ear impedances printed on the plot
  """
  ZearStr = "Z_earTop = {}".format(earImpedanceTop)
  if not args.one_face:
    ZearStr = ZearStr + "       Z_earBottom = {}".format(earImpedanceBottom)
  plt.text(0, 0.9*yrange, ZearStr, fontsize=10, bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'))
  """
  #code version printed on the plot
  #change back here
#  plt.text(0, -0.13*yrange, "Code version: {} {}".format(gitHash, gitDate[:-6]), fontsize=10)
  plt.savefig(outputFilename)
  print("Outputing graphical output into a file: " + outputFilename)


if args.debug:
  r1 = np.array([[staveTop.xLeft+60, staveTop.xLeft+165], [staveTop.yBottom-10, staveTop.yBottom-50]])
  dx = 412.5
  plt.figure(dpi=250)
  #plt.plot([r1[0][0], r1[0][0], r1[0][1], r1[0][1], r1[0][0]], [r1[1][0], r1[1][1], r1[1][1], r1[1][0], r1[1][0]], color = 'red', lw=.25)
  for i in range(14):
    plt.plot(dx*i + np.array(([r1[0][0], r1[0][0], r1[0][1], r1[0][1], r1[0][0]])), [r1[1][0], r1[1][1], r1[1][1], r1[1][0], r1[1][0]], color = 'red', lw=.25)
  plt.axvline(staveTop.xLeft, color='red', lw=.25)
  plt.axvline(staveTop.xRight, color='red', lw=.25)
  plt.axhline(staveTop.yTop, color='red', lw=.25)
  plt.axhline(staveTop.yBottom, color='red', lw=.25)

  for iregion, region in enumerate(staveTop.GetRegions('large')):
    xl, xr, yt, yb = region.getPosition()
    plt.plot([xl,xl],[yb,yt], color='magenta', lw=.25, alpha=0.7)
    plt.plot([xr,xr],[yb,yt], color='magenta', lw=.25, alpha=0.7)
    plt.plot([xl,xr],[yb,yb], color='magenta', lw=.25, alpha=0.7)
    plt.plot([xl,xr],[yt,yt], color='magenta', lw=.25, alpha=0.7)
    plt.text(xl+5, yt+50, f"{iregion}", color="white", fontsize=3)
    plt.text(xl+5, yt+100, f"t = {region.getAverageTemperature():.1f}", color='white', fontsize=3)
  for region in staveTop.GetRegions('ear'):
    xl, xr, yt, yb = region.getPosition()
    plt.plot([xl,xl],[yb,yt], color='goldenrod', lw=.25, alpha=0.7)
    plt.plot([xr,xr],[yb,yt], color='goldenrod', lw=.25, alpha=0.7)
    plt.plot([xl,xr],[yb,yb], color='goldenrod', lw=.25, alpha=0.7)
    plt.plot([xl,xr],[yt,yt], color='goldenrod', lw=.25, alpha=0.7)
    plt.text(xl+5, yt+100, f"t = {region.getAverageTemperature():.1f}", color='white', fontsize=3)

  temps = [region.getAverageTemperature() for region in staveTop.GetRegions('large')]
  mean = np.mean(temps)
  std = np.std(temps)
  plt.imshow(img_edges, vmin=(mean-2*std), vmax=(mean+10*std))
  plt.savefig("debug_output/edges.png")
