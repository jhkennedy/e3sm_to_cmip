# coding=utf-8
"""
CLDLIQ to clw converter
"""
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import logging
import os

import cdms2
import cmor


# list of raw variable names needed
RAW_VARIABLES = ['TGCLDIWP']

# output variable name
VAR_NAME = 'clivi'
VAR_UNITS = 'kg kg-1'

def handle(infiles, tables, user_input_path):
    """
    Transform E3SM.CLDLIQ into CMIP.clw

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
    clw = f(RAW_VARIABLES[0])
    lat = clw.getLatitude()[:]
    lon = clw.getLongitude()[:]
    lat_bnds = f('lat_bnds')
    lon_bnds = f('lon_bnds')
    time = clw.getTime()
    time_bnds = f('time_bnds')
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
    table = 'CMIP6_Amon.json'
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

    # write out the data
    try:
        for index, val in enumerate(clw.getTime()[:]):
            data = clw[index, :]
            cmor.write(
                varid,
                data,
                time_vals=val,
                time_bnds=[time_bnds[index, :]])
    except Exception as error:
        logging.error("Error in {}".format(VAR_NAME))
        return ""
    finally:
        cmor.close(varid)
    return VAR_NAME
