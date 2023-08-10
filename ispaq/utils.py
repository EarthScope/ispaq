"""
Utility functions for ISPAQ.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

import math
import os
import numpy as np
import pandas as pd
import sqlite3
from sqlite3 import Error
import datetime

from obspy import UTCDateTime


try:
    import irisseismic
    import evalresp as evresp
except:
    from . import irisseismic
    from . import evalresp as evresp

class EvalrespException(Exception):
    pass


# Utility functions ------------------------------------------------------------

def initialize_general_database_table(dbname, tablename, concierge):
    conn = sqlite3.connect(dbname)
    create_table_sql = """ CREATE TABLE IF NOT EXISTS """ + tablename + """ (
                            target text  NOT NULL,
                            value float NOT NULL,
                            start datetime  NOT NULL,
                            end datetime NOT NULL,
                            lddate datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(target, start, end)
                        ); """

    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        concierge.logger.error(e)
    conn.close()

def initialize_polcheck_database_table(dbname, concierge):
    conn = sqlite3.connect(dbname)
    create_table_sql = """ CREATE TABLE IF NOT EXISTS polarity_check (
                            target text  NOT NULL,
                            snclq2 text NOT NULL,
                            value float NOT NULL,
                            start datetime  NOT NULL,
                            end datetime NOT NULL,
                            lddate datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(target, start, end)
                        ); """

    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        concierge.logger.error(e)
    conn.close()

def initialize_trfunc_database_table(dbname, concierge):
    conn = sqlite3.connect(dbname)
    create_table_sql = """ CREATE TABLE IF NOT EXISTS transfer_function (
                            target text  NOT NULL,
                            gain_ratio float NOT NULL,
                            phase_diff float NOT NULL,
                            ms_coherence float NOT NULL,
                            start datetime  NOT NULL,
                            end datetime NOT NULL,
                            lddate datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(target, start, end)
                        ); """

    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        concierge.logger.error(e)
    conn.close()
    
def initialize_orcheck_database_table(dbname, concierge):
    conn = sqlite3.connect(dbname)
    create_table_sql = """ CREATE TABLE IF NOT EXISTS orientation_check (
                            target text  NOT NULL,
                            azimuth_R float NOT NULL,
                            backAzimuth float NOT NULL,
                            azimuth_Y_obs float NOT NULL,
                            azimuth_X_obs float NOT NULL,
                            azimuth_Y_meta float NOT NULL,
                            azimuth_X_meta float NOT NULL,
                            max_Czr float NOT NULL,
                            max_C_zr float NOT NULL,
                            magnitude float NOT NULL,
                            start datetime  NOT NULL,
                            end datetime NOT NULL,
                            lddate datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(target, start, end)
                        ); """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        concierge.logger.error(e)
    conn.close()
   
def initialize_psd_database_table(dbname, concierge, metric):

    conn = sqlite3.connect(dbname)
    create_table_sql = f""" CREATE TABLE IF NOT EXISTS {metric} (
                            target text  NOT NULL,
                            frequency float NOT NULL,
                            power float NOT NULL,
                            start datetime  NOT NULL,
                            end datetime NOT NULL,
                            lddate datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(target, frequency, start)
                        ); """

    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        concierge.logger.error(e)
    conn.close()
    
def initialize_pdf_database_table(dbname, concierge, correction_type):
    conn = sqlite3.connect(dbname)
    create_table_sql = f""" CREATE TABLE IF NOT EXISTS pdf_{correction_type} (
                            target text  NOT NULL,
                            frequency float NOT NULL,
                            power float NOT NULL,
                            hits float NOT NULL,
                            start datetime  NOT NULL,
                            end datetime NOT NULL,
                            lddate datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(target, frequency, power, start, end)
                        ); """

    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        concierge.logger.error(e)
    conn.close()


def insert_general_database_table(dbname, tablename, row):
    conn = sqlite3.connect(dbname)
    insert_sql = f'''INSERT INTO {tablename} (target, value, start, end)
  VALUES (?, ?, ?, ?) 
  ON CONFLICT(target, start, end) 
  DO UPDATE SET value=excluded.value, lddate=excluded.lddate;
  '''

    newRow = (row['target'], row['value'], row['start'],  row['end']);
    
    cur = conn.cursor()
    try:
        cur.execute(insert_sql, newRow)
    except:
        insert_sql = "INSERT or REPLACE INTO "  + tablename + " (target, value, start, end) VALUES (?, ?, ?, ?)"
        cur.execute(insert_sql, newRow)
             
    conn.commit()
    conn.close()

def insert_polcheck_database_table(dbname, row):
    conn = sqlite3.connect(dbname)
    insert_sql = f'''INSERT INTO polarity_check (target, snclq2, value, start, end)
  VALUES (?, ?, ?, ?, ?) 
  ON CONFLICT(target, start, end) 
  DO UPDATE SET snclq2=excluded.snclq2, value=excluded.value, lddate=excluded.lddate;
  '''
    newRow = (row['target'], row['snclq2'], row['value'], row['start'],  row['end']);
    
    cur = conn.cursor()
    try:
        cur.execute(insert_sql, newRow)
    except:
        insert_sql = "INSERT or REPLACE INTO polarity_check (target, snclq2, value, start, end) VALUES (?, ?, ?, ?, ?)"
        cur.execute(insert_sql, newRow)
    conn.commit()
    conn.close()
    
def insert_trfunc_database_table(dbname, row):
    conn = sqlite3.connect(dbname)
    insert_sql = f'''INSERT INTO transfer_function (target, gain_ratio, phase_diff, ms_coherence, start, end)
  VALUES (?, ?, ?, ?, ?, ?) 
  ON CONFLICT(target, start, end) 
  DO UPDATE SET gain_ratio=excluded.gain_ratio, phase_diff=excluded.phase_diff, ms_coherence=excluded.ms_coherence, lddate=excluded.lddate;
  '''
    newRow = (row['target'], row['gain_ratio'], row['phase_diff'], row['ms_coherence'], row['start'],  row['end']);
    
    cur = conn.cursor()
    try:
        cur.execute(insert_sql, newRow)
    except:
        insert_sql = "INSERT or REPLACE INTO transfer_function (target, gain_ratio, phase_diff, ms_coherence, start, end) VALUES (?, ?, ?, ?, ?, ?)"
        cur.execute(insert_sql, newRow)
    conn.commit()
    conn.close()
    
def insert_orcheck_database_table(dbname, row):
    conn = sqlite3.connect(dbname)
    insert_sql = f'''INSERT INTO orientation_check (target, azimuth_R, backAzimuth, azimuth_Y_obs, azimuth_X_obs, azimuth_Y_meta,
                     azimuth_X_meta, max_Czr, max_C_zr, magnitude, start, end)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
  ON CONFLICT(target, start, end) 
  DO UPDATE SET azimuth_R=excluded.azimuth_R, backAzimuth=excluded.backAzimuth, azimuth_Y_obs=excluded.azimuth_Y_obs,
  azimuth_X_obs=excluded.azimuth_X_obs, azimuth_X_meta=excluded.azimuth_X_meta, max_Czr=excluded.max_Czr, max_C_zr=excluded.max_C_zr,
  magnitude=excluded.magnitude, lddate=excluded.lddate;
  '''
    newRow = (row['target'], row['azimuth_R'], row['backAzimuth'], row['azimuth_Y_obs'], row['azimuth_X_obs'], row['azimuth_Y_meta'], row['azimuth_X_meta'], row['max_Czr'], row['max_C_zr'], row['magnitude'], row['start'], row['end'])
    
    cur = conn.cursor()
    try:
        cur.execute(insert_sql, newRow)
    except:
        insert_sql = """INSERT or REPLACE INTO orientation_check (target, azimuth_R, backAzimuth, azimuth_Y_obs, azimuth_X_obs, azimuth_Y_meta,
                     azimuth_X_meta, max_Czr, max_C_zr, magnitude, start, end) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        cur.execute(insert_sql, newRow)
    conn.commit()
    conn.close()
       
def insert_psd_database_table(dbname, row, metric):
    conn = sqlite3.connect(dbname)
    insert_sql = f'''INSERT INTO {metric} (target, frequency, power, start, end)
  VALUES (?, ?, ?, ?, ?) 
  ON CONFLICT(target, frequency, start, end) 
  DO UPDATE SET power=excluded.power, lddate=excluded.lddate;
  '''
    newRow = (row['target'], row['frequency'], row['power'], row['starttime'],  row['endtime'])

    cur = conn.cursor()
    
    try:
        cur.execute(insert_sql, newRow)
        
    except:
        insert_sql = f"INSERT or REPLACE INTO {metric} (target, frequency, power, start, end) VALUES (?, ?, ?, ?, ?)"
        cur.execute(insert_sql, newRow)
    conn.commit()
    conn.close()
 
def insert_pdf_database_table(dbname, row, target, starttime, endtime, correction_type):
    conn = sqlite3.connect(dbname)
    insert_sql = f'''INSERT INTO pdf_{correction_type} (target, frequency, power, hits, start, end)
  VALUES (?, ?, ?, ?, ?,?) 
  ON CONFLICT(target, frequency, power, start, end) 
  DO UPDATE SET hits=excluded.hits, lddate=excluded.lddate;
  '''
    newRow = (target, row['frequency'],row['power'], row['hits'], starttime, endtime)
     
    cur = conn.cursor()
    try:
        cur.execute(insert_sql, newRow)
    except:
        insert_sql = f"INSERT or REPLACE INTO pdf_{correction_type} (target, frequency, power, hits, start, end) VALUES (?, ?, ?, ?, ?, ?)"
        cur.execute(insert_sql, newRow)
    conn.commit()
    conn.close()
     

 
def retrieve_psd_unique_targets(dbname, sncl_pattern, starttime, endtime, logger, correction_type):

    conn = sqlite3.connect(dbname)
    select_sql = f"SELECT DISTINCT target from psd_{correction_type} WHERE target like '" + sncl_pattern +"'"
    if not starttime == "":
        select_sql = select_sql + " AND start >= '" + str(starttime).split('.')[0] + "'"
    if not endtime == "":
        select_sql = select_sql + " AND end <= '" + str(endtime).split('.')[0] + "'"
        
    select_sql = select_sql + ";"
    
    cur = conn.cursor()
    cur.execute(select_sql)
    records = [ str(i).strip('()').strip(',').strip("'") for i in cur.fetchall()]
    
    return records
    
def write_simple_df(df, filepath, concierge, sigfigs=6):
    """
    Write a pretty dataframe with appropriate significant figures to a .csv file.
    :param df: Dataframe of simpleMetrics.
    :param filepath: File to be created.
    :param sigfigs: Number of significant figures to use.
    :return: status
    """
    
    output = concierge.output
    dbname = concierge.db_name

    
    if df is None:
        raise("Dataframe of simple metrics does not exist.")
    # Sometimes 'starttime' and 'endtime' get converted from UTCDateTime to float and need to be
    # converted back. Nothing happens if this column is already of type UTCDateTime.
    df.starttime = df.starttime.apply(UTCDateTime, precision=0) # no milliseconds
    df.endtime = df.endtime.apply(UTCDateTime, precision=0) # no milliseconds
    df = df.replace('NULL',np.nan)
    #df.loc[~df['metricName'].str.match('timing_quality') & df['value'].str.match('NULL'),'value'] = np.nan

    # Get pretty values
    pretty_df = format_simple_df(df, sigfigs=sigfigs)
    pretty_df = pretty_df.rename(index=str,columns={'snclq':'target','starttime':'start','endtime':'end'})
    # Reorder columns, putting non-standard columns at the end and omitting 'qualityFlag'
    columns = ['target','start','end','metricName']
    original_columns = pretty_df.columns
    extra_columns = sorted(list( set(original_columns).difference(set(columns)) ))
    extra_columns.remove('qualityFlag')
#     if "time" in extra_columns:
#         extra_columns.remove('time')

    columns.extend(extra_columns)
    
    pretty_df.drop_duplicates(inplace=True)
    
    # Write out to database or .csv file
    if output == 'csv':
        pretty_df[columns].to_csv(filepath, index=False)
    elif output == 'db':
        for a,row in pretty_df.iterrows():
            tablename = row['metricName']

            if tablename == 'transfer_function':
                initialize_trfunc_database_table(dbname, concierge)
                insert_trfunc_database_table(dbname, row)
            elif tablename == 'orientation_check':
                initialize_orcheck_database_table(dbname, concierge)
                insert_orcheck_database_table(dbname, row)
            elif tablename == 'polarity_check':
                initialize_polcheck_database_table(dbname, concierge)
                insert_polcheck_database_table(dbname, row)
            else:
                initialize_general_database_table(dbname, tablename, concierge)
                insert_general_database_table(dbname, tablename, row)
    # No return value

def format_simple_df(df, sigfigs=6):
    """
    Create a pretty dataframe with appropriate significant figures.
    :param df: Dataframe of simpleMetrics.
    :param sigfigs: Number of significant figures to use.
    :return: Dataframe of simpleMetrics.
    
    The following conversions take place:
    
    * Round the 'value' column to the specified number of significant figures.
    * Convert 'starttime' and 'endtime' to python 'date' objects.
    """
    
    if 'value' in df.columns:
        # convert values to float
        df.value = df.value.astype(float)
        format_string = "." + str(sigfigs) + "g"
        df.value = df.value.apply(lambda x: format(x, format_string))
        df.value = df.value.astype(str)
        df.loc[df['metricName'].str.match('timing_quality') & df['value'].str.match('nan'),'value'] = 'NULL'
    if 'starttime' in df.columns:
        df.starttime = df.starttime.apply(UTCDateTime, precision=0) # no milliseconds
        df.starttime = df.starttime.apply(lambda x: x.strftime("%Y-%m-%dT%H:%M:%S"))
    if 'endtime' in df.columns:
        df.endtime = df.endtime.apply(UTCDateTime, precision=0) # no milliseconds
        df.endtime = df.endtime.apply(lambda x: x.strftime("%Y-%m-%dT%H:%M:%S"))
    if 'qualityFlag' in df.columns:
        
        df.qualityFlag = df.qualityFlag.astype(int)


    return df   
  
def write_numeric_df(df, filepath, concierge, metric, sigfigs=6):
    """
    Write a pretty dataframe with appropriate significant figures to a .csv file.
    :param df: PSD dataframe.
    :param filepath: File to be created.
    :param sigfigs: Number of significant figures to use.
    :return: status
    """

    output = concierge.output
    dbname = concierge.db_name

    # Get pretty values
    pretty_df = format_numeric_df(df, sigfigs=sigfigs)
    # Write out to db or .csv file
    if output == 'csv':
        pretty_df.to_csv(filepath, index=False)
    elif output == 'db':

        initialize_psd_database_table(dbname, concierge, metric)
        for ind,row in pretty_df.iterrows():
            insert_psd_database_table(dbname, row, metric)
    # No return value

def write_pdf_df(df, filepath, iappend, sncl, starttime, endtime, concierge, correction_type, sigfigs=6):
    """
    Write a pretty dataframe with appropriate significant figures to a .csv file.
    :param df: PSD dataframe.
    :param filepath: File to be created.
    :param sigfigs: Number of significant figures to use.
    :return: status
    """
    
    ##### THIS SECTION NEEDS UPDATING, AND NEW INITIALIZE AND INSERT FUNCTIONS #####
    output = concierge.output
    dbname = concierge.db_name
    
    # Get pretty values
    pretty_df = format_numeric_df(df, sigfigs=sigfigs)

    # Write out to db or .csv file
    if output == 'csv':
        if iappend == 'a':
            pretty_df.to_csv(filepath, mode='a', index=False)
        else:
            pretty_df.to_csv(filepath, index=False)
    elif output == 'db':
        initialize_pdf_database_table(dbname, concierge, correction_type)
        for ind,row in pretty_df.iterrows():
            insert_pdf_database_table(dbname, row, sncl, str(starttime), str(endtime),correction_type)
    # No return value

def format_numeric_df(df, sigfigs=6):
    """
    Create a pretty dataframe with appropriate significant figures.
    :param df: Dataframe with only UTCDateTimes or numeric.
    :param sigfigs: Number of significant figures to use.
    :return: Dataframe of simpleMetrics.
    
    The following conversions take place:
    
    * Round the 'value' column to the specified number of significant figures.
    * Convert 'starttime' and 'endtime' to python 'date' objects.
    """

    format_string = "." + str(sigfigs) + "g"
    for column in df.columns:
        if column == 'starttime':
            df.starttime = df.starttime.apply(UTCDateTime, precision=0) # no milliseconds
            df.starttime = df.starttime.apply(lambda x: x.strftime("%Y-%m-%dT%H:%M:%S"))
        elif column == 'endtime':
            df.endtime = df.endtime.apply(UTCDateTime, precision=0) # no milliseconds
            df.endtime = df.endtime.apply(lambda x: x.strftime("%Y-%m-%dT%H:%M:%S"))
        elif column == 'target':
            pass # 'target' is the SNCL Id
        else:
            df[column] = df[column].astype(float)
            df[column] = df[column].apply(lambda x: format(x, format_string))
            df[column] = df[column].astype(str)
            
    return df   
  
def get_slot(r_object, prop):
    """
    Return a property from the R_Stream.
    :param r_object: IRISSeismic Stream, Trace or TraceHeader object
    :param prop: Name of slot in the R object or any child object
    :return: python version value contained in the named property (aka 'slot')
    
    This convenience function allows business logic code to easily extract
    any property that is an atomic value in one of the R objects defined in
    the IRISSeismic R package.
    
    IRISSeismic slots as of 2016-04-07
    
    stream_slots = r_stream.slotnames()
     * url
     * requestedStarttime
     * requestedEndtime
     * act_flags
     * io_flags
     * dq_flags
     * timing_qual
     * traces
    
    trace_slots = r_stream.do_slot('traces')[0].slotnames()
     * stats
     * Sensor
     * InstrumentSensitivity
     * InputUnits
     * data
    
    stats_slots = r_stream.do_slot('traces')[0].do_slot('stats').slotnames()
     * sampling_rate
     * delta
     * calib
     * npts
     * network
     * location
     * station
     * channel
     * quality
     * starttime
     * endtime
     * processing
    """
    
    slotnames = list(r_object.slotnames())
    
    # R Stream object
    if 'traces' in slotnames:
        if prop in ['traces']:
            # return traces as R objects
            return r_object.do_slot(prop)
        elif prop in ['requestedStarttime','requestedEndtime']:
            # return times as UTCDateTime
            return UTCDateTime(r_object.do_slot(prop)[0])
        elif prop in slotnames:
            # return atmoic types as is
            return r_object.do_slot(prop)[0]
        else:
            # looking for a property from from lower down the hierarchy
            r_object = r_object.do_slot('traces')[0]
            slotnames = list(r_object.slotnames())            
        
    # R Trace object
    if 'stats' in slotnames:
        if prop in ['stats']:
            # return stats as an R object
            return r_object.do_slot(prop)
        elif prop in ['data']:
            # return data as an array
            return list(r_object.do_slot(prop))
        elif prop in slotnames:
            # return atmoic types as is
            return r_object.do_slot(prop)[0]
        else:
            # looking for a property from from lower down the hierarchy
            r_object = r_object.do_slot('stats')
            slotnames = list(r_object.slotnames())
    
    # R TraceHeader object
    if 'processing' in slotnames:
        if prop in ['starttime','endtime']:
            # return times as UTCDateTime
            return UTCDateTime(r_object.do_slot(prop)[0])
        else:
            # return atmoic types as is
            return r_object.do_slot(prop)[0]
    
    
    # Should never get here
    raise('"%s" is not a recognized slot name' % (prop))
        
def getSpectra(st, sampling_rate, metric, concierge):
    # This function returns an evalresp fap response needed for PSD calculation 
    # for trace st using sampling_rate to determine frequency limits
    #
    # metric=transferFunction sets units="def" 
    # metric=PSD sets units="acc" 
    #
    # set respDir to the directory containing RESP files to run evalresp locally

    if sampling_rate is None:
       raise Exception("no sampling_rate was passed to getSpectra")

    if (math.isnan(sampling_rate)):
       raise Exception("no sampling_rate was passed to getSpectra")   

    # Min and Max frequencies for evalresp will be those used for the cross spectral binning
    alignFreq = 0.1

    if (sampling_rate <= 1):
        loFreq = 0.001
    elif (sampling_rate > 1 and sampling_rate < 10):
        loFreq = 0.0025
    else:
        loFreq = 0.005

    # No need to exceed the Nyquist frequency after decimation
    hiFreq = 0.5 * sampling_rate

    log2_alignFreq = math.log(alignFreq,2)
    log2_loFreq = math.log(loFreq,2)
    log2_hiFreq = math.log(hiFreq,2)

    if alignFreq >= hiFreq:
        octaves = []
        octave = log2_alignFreq
        while octave >= log2_loFreq:
            if octave <= log2_hiFreq:
                octaves.append(octave)
            octave -= 0.125
        octaves = pd.Series(octaves).sort_values().reset_index(drop=True)
    else:
        octaves = []
        octave = log2_alignFreq
        loOctaves = []
        while octave >= log2_loFreq:
            loOctaves.append(octave)
            octave -= 0.125
        loOctaves = pd.Series(loOctaves)
            
        octave = log2_alignFreq
        hiOctaves = []
        while octave <= log2_hiFreq:
            hiOctaves.append(octave)
            octave += 0.125
        hiOctaves = pd.Series(hiOctaves)
            
        octaves = loOctaves.append(hiOctaves).drop_duplicates().sort_values().reset_index(drop=True)
        
    binFreq = pow(2,octaves)

    # Arguments for evalresp
    minfreq = min(binFreq)
    maxfreq = max(binFreq)
    nfreq = len(binFreq)
    if (metric == "transferFunction"):
        units = 'DEF'
    if (metric == "PSD"):
        units = 'ACC'
    output = 'FAP'

    network = get_slot(st,'network')
    station = get_slot(st,'station')
    location = get_slot(st,'location')
    channel = get_slot(st,'channel')
    starttime = get_slot(st,'starttime')
  
    # REC - invoke evalresp either programmatically from a RESP file or by invoking the web service 

    evalResp = None
    respDir = concierge.resp_dir

    if (respDir):
        # calling local evalresp -- generate the target file based on the SNCL identifier
        # file pattern:  RESP.<NET>.<STA>.<LOC>.<CHA> or RESP.<STA>.<NET>.<LOC>.<CHA>
        localFile = os.path.join(respDir,".".join(["RESP", network, station, location, channel])) # attempt to find the RESP file
        localFile2 = os.path.join(respDir,".".join(["RESP", station, network, location, channel])) # alternate pattern
        for localFiles in (localFile, localFile + ".txt", localFile2, localFile2 + ".txt"):
            if (os.path.exists(localFiles)):
                concierge.logger.debug('Found local RESP file %s' % localFiles)
                debugMode = False

                try:
                    evalResp = evresp.getEvalresp(localFiles, network, station, location, channel, starttime,
                                       minfreq, maxfreq, nfreq, units.upper(), output.upper(), "LOG", debugMode)
                except Exception as e:
                    raise 

                if evalResp is not None:
                    break   # break early from loop if we found a result
        if evalResp is None:
            raise EvalrespException('No RESP file found at %s[.txt] or %s[.txt]' % (localFile,localFile2))

    else:    
        # calling the web service 
        concierge.logger.debug('calling IRIS evalresp web service')
        try:
            evalResp = irisseismic.getEvalresp(concierge.dataselect_url, concierge.dataselect_type, network, station, location, channel, starttime,
                                       minfreq, maxfreq, nfreq, units.lower(), output.lower())
        except Exception as e:
            raise
    return(evalResp)

def getSampleRateSpectra(r_stream,sampling_rate,norm_freq, concierge):

    if sampling_rate is None or math.isnan(sampling_rate):
       raise Exception("no data sampling rate was available")

    if norm_freq is None or math.isnan(norm_freq):
       raise Exception("no metadata sensitivity was available")

    minfreq = norm_freq/10
    maxfreq = 10*sampling_rate
    nfreq = math.ceil(np.log10(maxfreq/minfreq)*100)
    units = 'def'
    output = 'fap'

    # need to create new function here, to avoid cut and paste
    network = get_slot(r_stream,'network')
    station = get_slot(r_stream,'station')
    location = get_slot(r_stream,'location')
    channel = get_slot(r_stream,'channel')
    starttime = get_slot(r_stream,'starttime')

    evalResp = None
    respDir = concierge.resp_dir

    concierge.logger.debug('minfreq %f, maxfreq %f, nfreq %f' % (minfreq,maxfreq,nfreq))

    if (respDir):
        # calling local evalresp -- generate the target file based on the SNCL identifier
        # file pattern:  RESP.<NET>.<STA>.<LOC>.<CHA> or RESP.<STA>.<NET>.<LOC>.<CHA>
        localFile = os.path.join(respDir,".".join(["RESP", network, station, location, channel])) # attempt to find the RESP file
        localFile2 = os.path.join(respDir,".".join(["RESP", station, network, location, channel])) # alternate pattern
        for localFiles in (localFile, localFile + ".txt", localFile2, localFile2 + ".txt"):
            if (os.path.exists(localFiles)):
                concierge.logger.debug('Found local RESP file %s' % localFiles)
                debugMode = False

                try:
                    evalResp = evresp.getEvalresp(localFiles, network, station, location, channel, starttime,
                                       minfreq, maxfreq, nfreq, units.upper(), output.upper(), "LOG", debugMode)
                except Exception as e:
                    raise

                if evalResp is not None:
                    break   # break early from loop if we found a result
        if evalResp is None:
            raise EvalrespException('No RESP file found at %s[.txt] or %s[.txt]' % (localFile,localFile2))

    else:
        # calling the web service
        try:
            evalResp = irisseismic.getEvalresp(concierge.dataselect_url, concierge.dataselect_type, network, station, location, channel, starttime,
                                       minfreq, maxfreq, nfreq, units.lower(), output.lower())
        except Exception as e:
            raise
    return(evalResp)

    

# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)


