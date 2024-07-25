import os
import time
import subprocess
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
from itertools import compress

global fileList
global dirmemory
global confirmToken

fileList = []
dirmemory = "/"
confirmToken = False

def browseFiles():
    global fileList
    global dirmemory

    #list of files
    fileList = filedialog.askopenfilenames(initialdir = dirmemory, title = "Select a File", filetypes = (("numpy.savez","*.npz*"),("all files","*.*")))

    #use the name of the first file in the list to find the containing folder for all files in fileList
    if len(fileList) > 0:
        dirmemory = os.path.commonpath([fileList[0], fileList[1]])
        directory.set(dirmemory + "/output")

    print("files: \n")
    print(str(fileList).replace(" ","\n\n"))

    #notification of action
    print("File explorer is open at location: " + dirmemory)
    label_file_explorer.configure(text= str(len(fileList)) + " Files Opened at: " + dirmemory)

def analyze():
    if confirmToken and len(fileList) > 0:
        to_execute0, to_execute1 = parseVars()
        starting_directory = "./ThermalImpedanceQA"
        startTime = time.time()
        numFiles = len(fileList)
        average = 0

        for i in fileList:
            startwatch = time.time()
            executable_command = to_execute0 + '"' + i + '"' + to_execute1

            fileName = i[i.rindex("/"):]

            print("\nCOMMAND TO EXECUTE: ")
            print(executable_command + "\n")

            label_file_explorer.configure(text= " Analyzing file: " + fileName)
            label_file_explorer.update()

            process = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", executable_command],
                cwd=starting_directory,
                capture_output=True,  # Capture output for further processing (optional)
            )

            # Check for errors
            if process.returncode == 0:
                # Access captured output if needed
                output = process.stdout.decode()
                print(output)
            else:
                print(f"Error running Powershell command: {process.stderr.decode()}")
            
            average += (time.time() - startwatch)/numFiles


        timeElapsed = round(time.time() - startTime, 8)
        label_file_explorer.configure(text=
                                      "All files done and ready for next batch. Time elapsed: " + str(timeElapsed) + " seconds. Average time per file: " + str(average) + " seconds.")
        
        reenable()

    elif not confirmToken:
        label_file_explorer.configure(text="Please confirm your settings first. ")

    elif not len(fileList) > 0:
        label_file_explorer.configure(text="Please select some files to analyze!")

def parseVars():
    initialParams0 = ['python', 'impedanceFromCSV.py']
    initialParams1 = ['"../npz-template.cfg"']
    initialParams2 = ["-g", "-1f", "-d", "--kill-shiny", "--adc"]

    orientationMod = [[''], ['--orientation', 'L'], ['--orientation', 'J'], ['--orientation', 'K']]
    initialParams1.extend(orientationMod[orientation.get()])

    if directory.get() != "./output":
        initialParams1.extend(["-o", '"' + directory.get() + '"'])

    if float(emissivity.get()) != 0.92:
        initialParams1.extend(["--emissivity", str(emissivity.get())])

    if float(ntrim.get()) != 0:
        initialParams1.extend(["--nTrim", str(ntrim.get())])

    boolParamsMod = [True, singleFace.get(), debug.get(), killEmissivity.get(), adc.get()]
    initialParams2 = list(compress(initialParams2, boolParamsMod))

    if manualBoundaries.get():
        r_boundsFull = any(float(i.get()) != 0 for i in right_boundaries)
        l_boundsFull = any(float(i.get()) != 0 for i in left_boundaries)
        
        if not singleFace.get():
            bounds = right_boundaries + left_boundaries
        elif r_boundsFull:
            bounds = right_boundaries
        elif l_boundsFull:
            bounds = left_boundaries

        boundaries = ' '.join([i.get() for i in bounds])

        initialParams1.extend(["--manual_boundaries", boundaries])

    initialParams1 = initialParams1 + initialParams2

    to_execute0 = ' ' + ' '.join([str(i) for i in initialParams0]) + ' '
    to_execute1 = ' ' + ' '.join([str(i) for i in initialParams1])

    #print(initialParams0, initialParams1)
    #print(to_execute0, to_execute1)

    return to_execute0, to_execute1

def reenable():
    widgetList = borders_frame.winfo_children() + trim_frame.winfo_children() + orientation_frame.winfo_children() + emissivity_frame.winfo_children() + [textbox_outpath, label_outpath, button_debug, textbox_emissivity]
    enabledList = []

    analyze_button.configure(bg='dark slate gray', relief=SUNKEN, state='disabled')
    confirm_button.configure(bg='orange red',relief=RAISED, state='normal')

    for widget in widgetList:
        if not type(widget) in [Label, LabelFrame, Frame]:
            widget.configure(state='normal')
            print(widget.widgetName + " back online. ")
        enabledList.append(widget)

    trim_label.configure(fg="black")
    label_emissivity.configure(fg="black")
    label_outpath.configure(fg='black')

    print("\nSuccessfully reset. \n")

    return enabledList

def disable():
    widgetList = borders_frame.winfo_children() + trim_frame.winfo_children() + orientation_frame.winfo_children() + emissivity_frame.winfo_children() + [textbox_outpath, label_outpath, button_debug, textbox_emissivity]
    disabledList = []

    analyze_button.configure(bg='dark green', relief=RAISED, state='normal')
    confirm_button.configure(bg='coral4',relief=SUNKEN, state='disabled')

    for widget in widgetList:
        if not type(widget) in [Label, LabelFrame, Frame]:
            widget.configure(state='disabled')
            print(widget.widgetName + " successfully disabled. ")
            disabledList.append(widget)

    trim_label.configure(fg="grey")
    label_emissivity.configure(fg="grey")
    label_outpath.configure(fg='grey')

    print("\nReady to analyze. \n")

    return disabledList

def confirm():
    global confirmToken

    if not os.path.isdir(directory.get()):
        try:
            os.mkdir(directory.get())
        except:
            label_file_explorer.configure(text=
                                          "Please ensure the specified output path is a viable filepath.")
            print("Error. Output path invalid. ")
            return

    if manualBoundaries.get():
        for i in right_boundaries + left_boundaries:
            try:
                float(i.get())
            except:
                label_file_explorer.configure(text=
                                            "Please ensure all manual boundaries entered are numerical values.")
                print("Error: Non-numerical boundary value detected.")
                return
            
        r_boundsFull = any(float(i.get()) != 0 for i in right_boundaries)
        l_boundsFull = any(float(i.get()) != 0 for i in left_boundaries)
        
        if not r_boundsFull and not l_boundsFull:
            label_file_explorer.configure(text=
                                          "Error. Please enter manual bounds or deselect 'manual bounds' option.")
            return
        elif r_boundsFull and l_boundsFull and singleFace.get():
                label_file_explorer.configure(text=
                                              "Error. Please delete one set of boundaries or deselect the 'single face' option.")
                return
        elif r_boundsFull != l_boundsFull and not singleFace.get():
                label_file_explorer.configure(text=
                                              "Error. Please enter both sets of boundaries for a double-side configuration.")
                return
                
    try:
        float(emissivity.get())
    except:
        label_file_explorer.configure(text="Please ensure emissivity value is numerical.")
        print("Error: Non-numerical emissivity value detected.")
        return
    
    try:
        float(ntrim.get())
    except:
        label_file_explorer.configure(text="Please ensure nTrim value is numerical.")
        print("Error: Non-numerical nTrim value detected.")
        return
    
    label_file_explorer.configure(text="Argument variables successfully confirmed and locked in. ")
    
    disable()

    confirmToken = True

def reset():
    global confirmToken
    global fileList

    reenable()

    orientation.set(value=0)
    singleFace.set(value=False)
    emissivity.set(value="0.92")
    killEmissivity.set(value=False)
    debug.set(value=False)
    manualBoundaries.set(value=False)
    ntrim.set(value='0')
    adc.set(value=False)
    directory.set(value='\\')
    
    for i in range(4):
        left_boundaries[i].set(value='0')
        right_boundaries[i].set(value='0')

    confirmToken = False
    fileList = []

#######################################################################
#TKINTER STUFF BELOW

root = Tk()
#getting screen width and height of display
width= 1200
height= 500
#setting tkinter window size
root.geometry("%dx%d" % (width, height))

###################################################################
#TKINTER VARIABLES

directory = StringVar(value=dirmemory)

orientation = IntVar(value=0)
singleFace = BooleanVar(value=False)
emissivity = StringVar(value="0.92")
killEmissivity = BooleanVar(value=False)
debug = BooleanVar(value=False)
manualBoundaries = BooleanVar(value=False)
ntrim = StringVar(value='0')
adc = BooleanVar(value=False)

left_boundaries = [StringVar(value="0") for i in range(4)]
right_boundaries = [StringVar(value="0") for i in range(4)]
#for i in range(4):
#    var_l = StringVar(value="0") 
#    var_r = StringVar(value="0") 
#    left_boundaries.append(var_l)
#    right_boundaries.append(var_r)

#############################################
#SCARY TKINTER THINGY DEFINITIONS AND PLACEMENT ooooooOOOOOOOOOoooo

label_file_explorer = Label(root, height=1, width = 100, text="Batch Calculate Impedance for Thermal QC.", foreground="blue")

organization_frame = Frame(root)

controls_frame=LabelFrame(organization_frame, text="Controls")
button_explore = Button(controls_frame, text = "Browse Files", command = browseFiles, width=10, height=1, cursor= "hand2")
label_outpath = Label(controls_frame, text="Files writing to:", width=20, height=1)
textbox_outpath = Entry(controls_frame, textvariable = directory, width=20)
button_debug = Checkbutton(controls_frame, text="Run in debug mode", var=debug, width=20, height=1)
button_reset = Button(controls_frame, text = "Reset", command=reset, width=10, height=1, cursor = "hand2")
button_exit = Button(controls_frame, text = "Exit", command = exit, width=10, height=1, cursor= "hand2")

orientation_frame = LabelFrame(organization_frame, text="Orientation")
button_orientation_L = Radiobutton(orientation_frame, text="L-side", value=1, var=orientation, height=1)
button_orientation_J = Radiobutton(orientation_frame, text="J-side", value=2, var=orientation, height=1)
button_orientation_K = Radiobutton(orientation_frame, text="K-side", value=3, var=orientation, height=1)
button_singleFace = Checkbutton(orientation_frame, text="Single face", var=singleFace, height=1)

borders_frame=LabelFrame(organization_frame, text="Boundaries", width=1000, height=1200)
button_manual_boundaries = Checkbutton(borders_frame, text="use manual boundaries", width=20, height=1, var=manualBoundaries)

LeftSide_left = Entry(borders_frame, textvariable=left_boundaries[0], width=4)
LeftSide_top = Entry(borders_frame, textvariable=left_boundaries[2], width=4)
LeftSide_right = Entry(borders_frame, textvariable=left_boundaries[1], width=4)
LeftSide_bottom = Entry(borders_frame, textvariable=left_boundaries[3], width=4)

RightSide_left = Entry(borders_frame, textvariable=right_boundaries[0], width=4)
RightSide_top = Entry(borders_frame, textvariable=right_boundaries[2], width=4)
RightSide_right = Entry(borders_frame, textvariable=right_boundaries[1], width=4)
RightSide_bottom = Entry(borders_frame, textvariable=right_boundaries[3], width=4)

trim_frame = Frame(borders_frame)
n_trim = Entry(trim_frame, textvariable = ntrim, width=4)
trim_label = Label(trim_frame, text = "nTrim parameter", height=1)
trim_label.grid(column=0,padx=[0,5], row=0, sticky=E)
n_trim.grid(column=1,padx=[5,0],row=0, sticky=W)

pictures = [ImageTk.PhotoImage(Image.open(r'AtlStaveQAInfraRedAnalysis\ThermalImpedanceQA\build\assets\PXL_20240628_200312264.jpg').resize([80,160])), 
            ImageTk.PhotoImage(Image.open(r'AtlStaveQAInfraRedAnalysis\ThermalImpedanceQA\build\assets\PXL_20240628_200312264.jpg').resize([80,160]))]

RightSide_label = Label(borders_frame, image= pictures[0], width=100, height=175)
LeftSide_label = Label(borders_frame, image= pictures[1], width=100, height=175)
for i in range(7):
    borders_frame.columnconfigure(i)
for j in range(7):
    borders_frame.rowconfigure(j)

for i in range(5):
    organization_frame.columnconfigure(i)

emissivity_frame = LabelFrame(organization_frame, text="Emissivity")
button_normalize = Checkbutton(emissivity_frame, text="Normalize shininess", var = killEmissivity, height=1)
emissivity_val_frame = Frame(emissivity_frame)
textbox_emissivity = Entry(emissivity_val_frame, textvariable = emissivity, width=5)
label_emissivity = Label(emissivity_val_frame, text='Emissivity value: ')
button_adc = Checkbutton(emissivity_frame, text="ADC variables", var = adc, height=1)

processes_frame = Frame(organization_frame)
confirm_button = Button(processes_frame, text="Confirm Arguments", width=20,height=8, command = confirm, bg='orange red')
analyze_button = Button(processes_frame, text="Analyze!", width=20, height=8, command=analyze, bg="dark slate gray", fg='white', relief=SUNKEN, state='disabled')

label_file_explorer.pack(side=TOP, pady=[70,40])

organization_frame.pack(side=TOP)

controls_frame.grid(column=1, row=1, rowspan=2, sticky=E, padx=[0,5])
button_explore.pack(side=TOP, pady=[20,0])
button_reset.pack(side=TOP, pady=[0,5])
label_outpath.pack(side=TOP)
textbox_outpath.pack(side=TOP, pady=5)
button_debug.pack(side=TOP, pady=[0,5])
button_exit.pack(side=TOP, pady=[0,69])

orientation_frame.grid(column=2, row=1, sticky=S, padx=[5,5], pady=[0,5])
button_orientation_L.grid(row=0, pady=[10,0], sticky=W, padx=[30,76])
button_orientation_J.grid(row=1, sticky=W, padx=[30,75])
button_orientation_K.grid(row=2, sticky=W, padx=[30,75])
button_singleFace.grid(row=3, sticky=W, pady=[0,17], padx=[30,0])

emissivity_frame.grid(column=2, row=2, sticky=N, padx=[5,5], pady=[5,0])
emissivity_val_frame.grid(row=0, pady=[10,0])
button_normalize.grid(row=1, sticky=W, padx=[15,19])
button_adc.grid(row=2, pady=[0,15], sticky=W, padx=[15,0])

label_emissivity.pack(side=LEFT)
textbox_emissivity.pack(side=LEFT)

borders_frame.grid(column=3, row=1, columnspan=4, rowspan=2, sticky=W, padx=[5,5])
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

processes_frame.grid(column=7, row=1, rowspan=2, sticky=W, padx=[5,0])
confirm_button.pack(side=TOP, pady=[5,0])
analyze_button.pack(side=TOP, pady=[0,0])

root.mainloop()