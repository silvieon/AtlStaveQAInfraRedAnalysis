Hello! This is the text documentation for the Thermal QC Analysis code. 

HOW TO USE: 

--> open the file "impedanceFromCSV_visual V2" located in /ThermalImpedanceQA/build/. This should open VS Code. 

--> run the file by clicking the play button in the top right corner. 
    After letting the code run for a bit, this will open a new window with a bunch of buttons that looks like 2000s Internet.

--> click the "Browse Files" button in the top left of the window.

--> select all of the files you would like to analyze. 
    Keep in mind that these files must all be from the same trial, where the stave hasn't been moved between any of the files:
    Hot and cold data are fine to analyze together as long as the stave hasn't been moved in the dry box between any of the hot or cold cycles. 

--> input your parameters. 
    orientation: select whether you're analyzing data from a one-face setup (like the YWL setup prior to fall 2024) or from a two-face setup. 
                
                If one-face, select whether L-side or J-side; if two-face, select k-side. 
    
    emissivity: change this if you know the emissivity to be different from the default value. 
                
                Otherwise, assume it's the default.

    boundaries: use this if you want to define manual bounds for stave edges.
                
                You must check the box labeled "use manual boundaries" if you want to define manual bounds. 
                
                The text-entry boxes are oriented so that you may enter each boundary location for each stave edge in the box on the side where that boundary is. 
                For example, enter the left-side boundary of the J side mirror projection into the leftmost box. 
                
                If you have just a list of numbers, you can enter them into the boundary boxes in the order [left, right, top, bottom].
                    (if you only have four and not the full eight, just fill in some arbitrary side. It doesn't matter whether you fill in the left or the right.)
                
                The "nTrim parameter" is a marker for how many pixels the analysis code should shave off the outer edges of all images it sees.

                Debug mode gives more output in a debug output folder that helps show if the analysis code is working right or not. 

                You can change the place where the analysis outputs go by changing the text in "files writing to:".

--> once your analysis parameters are all done, hit "confirm variables" to lock everything in. 
    
    This will also check to make sure that all of your parameters are valid values. 

--> hit "analyze!". 
    This will, by default, put analysis outputs in a folder titled "output" next to all of the data files right where you found them.

--> hit "reset" to analyze a new batch of files. 

****NOTES****
The analysis script should generally run fine by itself. 
Parameters only need to be changed if the analysis script's default state screws up the analysis, as a general rule. 

~Silvia Wang, Tipton Group --- ATLAS ITK project at Yale Wright Labs. July 2024