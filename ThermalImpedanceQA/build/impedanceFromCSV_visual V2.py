import os
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import subprocess
import time

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
        file = fileList[0]
        filerev = file[::-1]
        filerev = filerev[filerev.find("/"):len(filerev)]
        dirmemory = filerev[::-1]
        directory.set(dirmemory + "/output")

    #notification of action
    print("File explorer is open at location: " + dirmemory)
    label_file_explorer.configure(text= str(len(fileList)) + " Files Opened at: " + dirmemory)
     

def analyze():
    if confirmToken:
        to_execute0, to_execute1 = parseVars()

        starting_directory = "./"
        print(starting_directory)

        startTime = time.time()

        for i in fileList:
            executable_command = to_execute0 + i + to_execute1

            fileName = i[::-1]
            fileName = fileName[0:fileName.find("/")]
            fileName = fileName[::-1]

            print("Analyzing file: " + fileName)
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

        timeElapsed = round(time.time() - startTime, 8)
        label_file_explorer.configure(text=
                                      "All files done. Ready for next batch. Time elapsed: " + str(timeElapsed) + " seconds.")
        
        reenable()

    else:
        label_file_explorer.configure(text="Please confirm your settings first. ")

def parseVars():
    initialParams0 = ['python', './ThermalImpedanceQA/impedanceFromCSV.py']
    initialParams1 = ["./npz-template.cfg", '--orientation']
    initialParams2 = ["-g", "--kill-shiny", "--nTrim",  "-d", "--adc", '-1f']

    match orientation.get():
        case 0:
            initialParams1.remove('--orientation')
        case 1:
            initialParams1.append('L')
        case 2:
            initialParams1.append('J')
        case 3:
            initialParams1.append('K')

    if not singleFace.get():
        initialParams2.remove('-1f')
    if not debug.get():
        initialParams2.remove('-d')
    if not killEmissivity.get():
        initialParams2.remove("--kill-shiny")
    if int(ntrim.get()) == 0:
        initialParams2.remove("--nTrim")
    if not adc.get():
        initialParams2.remove("--adc")

    if not directory.get() == "./output":
        initialParams1.extend(["-o", directory.get()])

    if manualBoundaries.get():
        r_boundsFull = any(int(i.get()) != 0 for i in right_boundaries)
        l_boundsFull = any(int(i.get()) != 0 for i in left_boundaries)
        if not r_boundsFull and not l_boundsFull:
            label_file_explorer.configure(text=
                                          "Error. Please enter manual bounds or deselect 'manual bounds' option.")
            return
        elif r_boundsFull and l_boundsFull:
            if singleFace.get():
                label_file_explorer.configure(text=
                                              "Error. Please delete one set of boundaries or deselect the 'single face' option.")
                return
            else:
                bounds = right_boundaries + left_boundaries
        elif r_boundsFull != l_boundsFull:
            if not singleFace.get():
                label_file_explorer.configure(text=
                                              "Error. Please enter both sets of boundaries for a double-side configuration.")
                return
            elif singleFace.get() and r_boundsFull:
                bounds = right_boundaries
            elif singleFace.get() and l_boundsFull:
                bounds = left_boundaries

        boundaries = ' '.join([i.get() for i in bounds])

        initialParams1.extend(["--manual_boundaries", boundaries])

    if not float(emissivity.get()) == 0.92:
        initialParams1.extend(["--emissivity", str(float(emissivity.get()))])

    initialParams1 = initialParams1 + initialParams2

    to_execute0 = ' ' + ' '.join([str(i) for i in initialParams0]) + ' '
    to_execute1 = ' ' + ' '.join([str(i) for i in initialParams1])

    print(initialParams0, initialParams1)
    print(to_execute0, to_execute1)

    return to_execute0, to_execute1

def reenable():
    widgetList = borders_frame.winfo_children() + trim_frame.winfo_children() + orientation_frame.winfo_children() + emissivity_frame.winfo_children()
    enabledList = []

    analyze_button.configure(bg = 'dark red')

    for widget in widgetList:
        if not type(widget) in [Label, LabelFrame, Frame]:
            if type(widget) == Entry:
                widget.configure(state='normal')
            else:
                widget.configure(state='active')
        enabledList.append(widget)

    trim_label.configure(fg="black")
    enabledList.append(trim_label)

    return enabledList

def disable():
    widgetList = borders_frame.winfo_children() + trim_frame.winfo_children() + orientation_frame.winfo_children() + emissivity_frame.winfo_children()
    disabledList = []

    analyze_button.configure(bg='dark green')

    for widget in widgetList:
        if not type(widget) in [Label, LabelFrame, Frame]:
            widget.configure(state='disabled')
            print(widget.widgetName + " successfully disabled. ")
            disabledList.append(widget)

    trim_label.configure(fg="grey")
    disabledList.append(trim_label)

    return disabledList

def confirm():
    global confirmToken

    if not os.path.isdir(directory.get()):
        try:
            os.mkdir(directory.get())
        except:
            label_file_explorer.configure(text=
                                          "Please ensure the specified output path is a viable filepath.")
            print("Error. Outpath not creatable. ")
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
                
    try:
        float(emissivity.get())
    except:
        label_file_explorer.configure(text="Please ensure emissivity value is numerical.")
        print("Error: Non-numerical emissivity value detected.")
        return
    
    label_file_explorer.configure(text="All argument variables confirmed and locked in. ")
    
    disable()

    confirmToken = True

def reset():
    global confirmToken

    reenable()

    orientation.set(value=0)
    singleFace.set(value=False)
    emissivity.set(value="0.92")
    killEmissivity.set(value=False)
    debug.set(value=False)
    manualBoundaries.set(value=False)
    ntrim.set(value='0')
    adc.set(value=False)
    for i in range(4):
        left_boundaries[i].set(value='0')
        right_boundaries[i].set(value='0')

    confirmToken = False

#######################################################################
#TKINTER STUFF BELOW

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

controls_frame=LabelFrame(root, text="Controls")
button_explore = Button(controls_frame, text = "Browse Files", command = browseFiles, width=10, height=1, cursor= "hand2")
label_outpath = Label(controls_frame, text="Files writing to:", width=20, height=1)
textbox_outpath = Entry(controls_frame, textvariable = directory, width=20)
button_debug = Checkbutton(controls_frame, text="Run in debug mode", var=debug, width=20, height=1)
button_reset = Button(controls_frame, text = "Reset", command=reset, width=10, height=1, cursor = "hand2")
button_exit = Button(controls_frame, text = "Exit", command = exit, width=10, height=1, cursor= "hand2")

orientation_frame = LabelFrame(root, text="Orientation")
button_orientation_L = Radiobutton(orientation_frame, text="L-side", value=1, var=orientation, width=10, height=1)
button_orientation_J = Radiobutton(orientation_frame, text="J-side", value=2, var=orientation, width=10, height=1)
button_orientation_K = Radiobutton(orientation_frame, text="K-side", value=3, var=orientation, width=10, height=1)
button_singleFace = Checkbutton(orientation_frame, text="Single face?", var=singleFace, width=20, height=1)

borders_frame=LabelFrame(root, text="Boundaries", width=1000, height=1200)
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
trim_label = Label(trim_frame, text = "nTrim parameter", width=20, height=1)
trim_label.pack(side=LEFT)
n_trim.pack(side=LEFT)

pictures = [ImageTk.PhotoImage(Image.open(r'AtlStaveQAInfraRedAnalysis\ThermalImpedanceQA\build\assets\PXL_20240628_200320287.jpg').resize([80,160])), 
            ImageTk.PhotoImage(Image.open(r'AtlStaveQAInfraRedAnalysis\ThermalImpedanceQA\build\assets\PXL_20240628_200312264.jpg').resize([80,160]))]

RightSide_label = Label(borders_frame, image= pictures[0], width=100, height=175)
LeftSide_label = Label(borders_frame, image= pictures[1], width=100, height=175)

weights = [2,2,2,1,2,2,2]
for i in range(7):
    borders_frame.columnconfigure(i)
for j in range(7):
    borders_frame.rowconfigure(j)

emissivity_frame = LabelFrame(root, text="Emissivity")
button_normalize = Checkbutton(emissivity_frame, text="Normalize shininess", var = killEmissivity, width=20, height=1)
textbox_emissivity = Entry(emissivity_frame, textvariable = emissivity, width=20)
button_adc = Checkbutton(emissivity_frame, text="ADC variables", var = adc, width=20, height=1)

processes_frame = Frame(root)
confirm_button = Button(processes_frame, text="Confirm Args", width=20,height=5, command = confirm, bg='dark orange')
analyze_button = Button(processes_frame, text="Analyze!", width=20, height=5, command=analyze, bg="dark red", fg="light grey")

label_file_explorer.grid(column=1, columnspan=5, row=1, sticky=W)

controls_frame.grid(column=1, row=2, sticky=N)
button_explore.pack(side=TOP, pady=[10,0])
label_outpath.pack(side=TOP)
textbox_outpath.pack(side=TOP, pady=3)
button_debug.pack(side=TOP)
button_reset.pack(side=TOP)
button_exit.pack(side=TOP, pady=[0,10])

orientation_frame.grid(column=2, row=2, sticky=N)
button_orientation_L.pack(side=TOP, pady=[10,0])
button_orientation_J.pack(side=TOP)
button_orientation_K.pack(side=TOP)
button_singleFace.pack(side=TOP)

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

processes_frame.grid(column=2, row=5, sticky=N)
confirm_button.pack(side=TOP)
analyze_button.pack(side=TOP)

root.mainloop()