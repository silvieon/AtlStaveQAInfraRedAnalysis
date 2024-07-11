#!/bin/bash

# Loop through files, replacing the variable part "..CERN_J_XXX.." in each filename
for i in $(seq -w 00 31); do
  # Construct the filename for each iteration
  filename="../Stave13_RaisedCore_Lowflow_v2_LS_CERN_L_0${i}.npz"
  filepng="Stave13_RaisedCore_Lowflow_v2_LS_CERN_L_0${i}_IMPEDANCES.png"
  
  # Run your Python script with the provided filename, configuration file, and other specified flags
  #python ./impedanceFromCSV.py "../Stave13_RaisedCore_Lowflow_v2_LS_CERN_L_000.npz" "../npz-template.cfg" -g -1f --orientation L --emissivity .92 -d
  
  python ./impedanceFromCSV.py "$filename" "../npz-template.cfg" -g -1f --orientation L --emissivity .92 -d
  
  #open output/${filepng}
  output/${filepng}
done  