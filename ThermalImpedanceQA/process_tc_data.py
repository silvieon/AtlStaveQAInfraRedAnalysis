#!/usr/bin/env python

import argparse
import numpy as np
from glob import glob
import os
import sys
import configparser
import itertools as it
import tempfile
import shutil
import subprocess

DEFAULT_TRANSMISSIVITY = 0.987
DEFAULT_TEMPERATURE_PROFILE='0.0000,0.0686,0.1233,0.1603,0.1969,0.2329,0.2685,0.3037,0.3385,0.3729,0.4068,0.4404,0.4736,0.5064,0.5395,0.5744,0.6088,0.6430,0.6770,0.7107,0.7441,0.7772,0.8099,0.8422,0.8742,0.905 -d8,0.9368,0.9681,1.0000'

DEFAULT_PARAMETERS = { "B":1452, "F":1.0, "O":-5208, "R2":0.016026809, "R1":17980.574, "AtomTemp":20.0, "ReflTemp":20.0, "Emissivity":.95, "Transmissivity": .987

}

#cold emissivity .905 -d
#hot emissivity .918

def adc_to_temp(adc_image, params):
    # CODE FROM ISU
    # converting DC counts received by each pixel of the IR camera,
    # which represents energy (heat), to temperature in degree C.
    params.setdefault('Transmissivity', DEFAULT_TRANSMISSIVITY)
    RawAtom = params["R1"] / (params["R2"] * ( np.exp( params["B"] / (params["AtomTemp"] + 273.15) ) - params["F"] ) ) - params["O"]
    RawRefl = params["R1"] / (params["R2"] * ( np.exp( params["B"] / (params["ReflTemp"] + 273.15) ) - params["F"] ) ) - params["O"]
    # old one before swapping RawAtom and Raw Refl RawObj_numerator   = ( adc_image - params["Transmissivity"] * (1 - params["Emissivity"]) * RawAtom - (1 - params["Transmissivity"]) * RawRefl )
    RawObj_numerator   = ( adc_image - params["Transmissivity"] * (1 - params["Emissivity"]) * RawRefl - (1 - params["Transmissivity"]) * RawAtom )
    RawObj_denominator = ( params["Emissivity"] * params["Transmissivity"])
    RawObj = RawObj_numerator / RawObj_denominator
    temp_img = params["B"] / np.log ( params["R1"] / ( params["R2"] * ( RawObj + params["O"] ) ) + params["F"] ) - 273.15

    return temp_img

def npz_images_to_temp(npz_images, emissivity=None):
    # convert images as stored in npz file into a single (averaged)
    # temperature map using the in-file metadata. override emissivity if provided.
    result = []
    for img, meta in npz_images:
        if emissivity is not None:
            meta['Emissivity'] = emissivity
        meta.setdefault('Transmissivity', DEFAULT_TRANSMISSIVITY)
        result.append(adc_to_temp(img, meta))
    return np.mean(result, axis=0)
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='path the thermal controller results')
    args = parser.parse_args()

    # first find the graphs file
    gfile = glob(os.path.join(args.path, 'graphs_*.npz'))
    if not len(gfile):
        print("Could not find graphs file in specified directory!")
        sys.exit(1)
    if len(gfile) > 1:
        print("Found more than one graphs file... i am confused!")
        sys.exit(1)
    gfile = gfile[0]

    # check whether we have a L or J side based on the graphs file name
    side_type = gfile[:-4].split('_')[-1]
    print("Side type is:", side_type)

    graphs = np.load(gfile)
    print("Loaded graphs file", gfile)
    print(list(graphs.keys()))

    # make interpolation functions to give input/output temp as a function of time
    temp_in = lambda t: np.interp(t, graphs['thermo_times'], graphs['thermo_data'][:,2])
    temp_out = lambda t: np.interp(t, graphs['thermo_times'], graphs['thermo_data'][:,3])
    flow_rate = lambda t: np.interp(t, graphs['flow_times'], graphs['flow_data'])
    print(graphs['flow_data'])

    # specific heat and density of hfe7100 a a function of temp [C]
    fluid_c = lambda T: 2*T + 1133
    fluid_density = lambda T: -2.2690*T + 1538.3

    def make_config(timestamp):
        config = configparser.ConfigParser()
        config.add_section('Default')
        regime = 'cold' if temp_in(timestamp) < 20 else 'hot'
        config.set('Default', 'regime', regime)
        config.set('Default', 'temp_in', str(temp_in(timestamp)))
        config.set('Default', 'temp_out', str(temp_out(timestamp)))
        tmean = 0.5*(temp_in(timestamp) + temp_out(timestamp))
        config.set('Default', 'c_liquid', str(fluid_c(tmean)))
        config.set('Default', 'liquid_density', str(fluid_density(tmean)))
        config.set('Default', 'flow_rate', str(flow_rate(timestamp)))
        config.set('Default', 'temperatureProfile', DEFAULT_TEMPERATURE_PROFILE)
        # hardcode EoS correction factors
        config.set('Default', 'dTdQ_large_0', str(1.193))
        config.set('Default', 'dTdQ_large_1', str(0.716))
        config.set('Default', 'dTdQ_small_0', str(0.591))
        config.set('Default', 'dTdQ_small_1', str(0.251))
        config.set('Default', 'dTdQ_nextEar', str(1.152))
        config.set('Default', 'nTrim', str(20))
        return config

    # load up the image files
    for fname in it.chain(
            glob(os.path.join(args.path, '*.npy')),
            glob(os.path.join(args.path, 'images_*.npz')),
        ):
        print(fname)
        out_path,out_name = os.path.split(fname)
        d = np.load(fname, allow_pickle=True)
        if fname.endswith('.npy'):
            temp_imgs = np.stack(list(it.starmap(adc_to_temp, d)), axis=0)
            timestamp = d[0,1]['timestamp']
        else:
            params = {k: v for k,v in d.items() if not k == 'images'}
            print('got params', params)
            temp_imgs = np.stack([adc_to_temp(img, params) for img in d['images']], axis=0)
            print('loaded temp_imgs', temp_imgs.shape)
            timestamp = params['timestamp']

        print('timestamp', timestamp)
        temp_img = temp_imgs.mean(axis=0)
        print(temp_img.shape)
        cfg = make_config(timestamp)
        with tempfile.TemporaryDirectory() as tempdir:
            print("temp dir:", tempdir)
            with open(os.path.join(tempdir, 'config.cfg'), 'w') as fcfg:
                cfg.write(fcfg)
            np.save(os.path.join(tempdir, 'image.npy'), temp_img)

            cmd=['python',
                './impedanceFromCSV.py',
                '-1f',
                f'-{side_type}',
                '--outpath',
                f'{tempdir}',
                f'{tempdir}/image.npy',
                f'{tempdir}/config.cfg',
            ]

            print(cmd)
            subprocess.run(cmd)

            shutil.copy(os.path.join(tempdir, 'image_IMPEDANCES.csv'),
                    os.path.join(out_path, out_name[:-4]+'_IMPEDANCES.csv'))