# coding=utf-8
"""
SOILICE to mrfso converter
"""
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import logging
import os

import cdms2
import cmor
import numpy as np


# list of raw variable names needed
RAW_VARIABLES = ['SOILICE']

# output variable name
VAR_NAME = 'mrfso'
VAR_UNITS = 'kg m-2'

def handle(infiles, tables, user_input_path):
    """
    Transform E3SM.SOILICE into CMIP.mrfso

    Parameters
    ----------
        infiles (List): a list of strings of file names for the raw input data
        tables (str): path to CMOR tables
        user_input_path (str): path to user input json file
    Returns
    -------
        var name (str): the name of the processed variable after processing is complete
    """

    msg = 'Starting {name}'.format(name=__name__)
    logging.info(msg)

    # extract data from the input file
    f = cdms2.open(infiles[0])
    ice = f(RAW_VARIABLES[0])
    lat = ice.getLatitude()[:]
    lon = ice.getLongitude()[:]
    lat_bnds = f('lat_bnds')
    lon_bnds = f('lon_bnds')
    time = ice.getTime()
    time_bnds = f('time_bounds')
    f.close()

    # setup cmor
    logfile = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(logfile):
        os.makedirs(logfile)
    logfile = os.path.join(logfile, VAR_NAME + '.log')
    cmor.setup(
        inpath=tables,
        netcdf_file_action=cmor.CMOR_REPLACE, 
        logfile=logfile)
    cmor.dataset_json(user_input_path)
    table = 'CMIP6_Lmon.json'
    try:
        cmor.load_table(table)
    except (Exception, BaseException):
        raise Exception('Unable to load table from {}'.format(__name__))

    # create axes
    axes = [{
        'table_entry': 'time',
        'units': time.units
    }, {
        'table_entry': 'latitude',
        'units': 'degrees_north',
        'coord_vals': lat[:],
        'cell_bounds': lat_bnds[:]
    }, {
        'table_entry': 'longitude',
        'units': 'degrees_east',
        'coord_vals': lon[:],
        'cell_bounds': lon_bnds[:]
    }]
    axis_ids = list()
    for axis in axes:
        axis_id = cmor.axis(**axis)
        axis_ids.append(axis_id)

    # create the cmor variable
    varid = cmor.variable(VAR_NAME, VAR_UNITS, axis_ids)

    # get the index for the levgrnd axis
    levgrnd_index = ice.getAxisIds().index('levgrnd')
    if levgrnd_index == -1:
        msg = 'Error finding levgrnd axis index'
        logging.error(msg)
        return None
    # when we actually use the index, it will be on a single slice of the time axis, reducing the index by one
    levgrnd_index = levgrnd_index - 1

    # write out the data
    try:
        for index, val in enumerate(ice.getTime()[:]):
            # create a mask so we can avoid places with no ice
            mask = np.greater(ice[index, :], 0.0)
            data = np.sum(
                ice[index, :],
                axis=levgrnd_index)
            capped = np.where(
                np.greater(data, 5000.0),
                5000.0,
                data)
            data = np.where(
                mask,
                capped,
                data)
            cmor.write(
                varid,
                data,
                time_vals=val,
                time_bnds=[time_bnds[index, :]])
    except Exception as error:
        logging.error("Error in {}".format(VAR_NAME))
    finally:
        cmor.close(varid)
    return VAR_NAME