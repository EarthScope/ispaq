#
# evalresp.py
# evalresp python driver as an addendum to obspy
#
# Robert Casey - IRIS - October 2016
# -- ideas and source code borrowed from Obspy invsim module
# ---- Copyright (C) 2008-2012 Moritz Beyreuther, Yannik Behr
# -- other ideas and source code extracted from evalresp
# ---- Copyright (C) 1997-2016 Incorporated Research Institutions for Seismology
# ---- Tom McSweeney, Chad Trabant, IRIS
# ---- Ilya Dricker, Eric Thomas, Sid Hellman, Andrew Cooke, ISTI
#
import os
import numpy as np
from obspy import UTCDateTime
from obspy.signal.headers import clibevresp
import ctypes as C
import math as M
import pandas as pd
#from future.utils import native_str
from obspy.core.util.base import NamedTemporaryFile




def getEvalresp(filename, network, station, location, channel, starttime,
                minfreq, maxfreq, nfreq, units, output, spacing, debug=False):
    """
    call to evalresp in the manner of MUSTANG R metrics calls to IRIS web services

    returns a data frame of frequency-sorted value columns, based on indicated output type.

    :type filename: str or file
    :param filename: SEED RESP-filename or open file like object with RESP
        information. Any object that provides a read() method will be
        considered to be a file like object.

    :type network: str
    :param network: Network id

    :type station: str
    :param station: Station id

    :type location: str
    :param location: Location id

    :type channel: str
    :param channel: Channel id

    :type starttime: :class:`~obspy.core.utcdatetime.UTCDateTime`
    :param starttime: Date of interest

    :type minfreq: float
    :param minfreq: minimum frequency to generate response from

    :type maxfreq: float
    :param maxfreq: maximum frequency to generate response from

    :type nfreq: int
    :param nfreq: number of steps between minfreq and maxfreq to analyze

    :type units: str
    :param units: units of measurement to represent ('DIS','VEL','ACC','DEF')

    :type output: str
    :param output: the style of output to present in data frame ('CS','FAP')
    
    :type spacing: str
    :param spacing: select 'LIN'ear or 'LOG'arithmic spacing of frequency steps
    
    :type debug: boolean
    :param debug: toggle to True to see verbose output from evalresp

    :rtype :class:`pd.DataFrame`
    :return data frame containing columns starting with frequency sorted ascending

    """
    # parameters translated to Obspy-style and ordering
    eval_tuple = evalresp(minfreq, maxfreq, nfreq, filename, starttime, station, channel,
                    network, location, units, debug, output, spacing)
    
    eval_df = pd.DataFrame.from_records(eval_tuple)
    eval_df = pd.DataFrame.transpose(eval_df)

    # add the column headers to the data frame
    if (output == "FAP"):
        eval_df.columns = ['freq','amp','phase']  # name the DF columns
        # to be comparative to ws/evalresp behavior, we must restrict the phase values
        # to 7 significant digits
        eval_df.phase = list(map(lambda x: float('{:.7g}'.format(x)),eval_df.phase))
        eval_df.freq = list(map(lambda x: float('{:.7g}'.format(x)),eval_df.freq))
        eval_df.amp = list(map(lambda x: float('{:.7g}'.format(x)),eval_df.amp))
    else:
        eval_df.columns = ['freq','real','imag']
    
    return eval_df


def evalresp(sfft, efft, nfft, filename, date, station='*', channel='*',
             network='*', locid='*', units="VEL",
             debug=False, output="FAP", spacing="LOG"):
    """
    Use the evalresp library to extract instrument response
    information from a SEED RESP-file.
    ...
    Modified from Obspy/signal/invsim.py
    Allow for output type to be altered between CS, FAP.
    Allow for min and max frequency to be specified.

    :type sfft: float
    :param sfft: starting frequency for FFT

    :type efft: float
    :param efft: ending frequency for FFT

    :type nfft: int
    :param nfft: Number of FFT points between sfft and efft

    :type filename: str or file
    :param filename: SEED RESP-filename or open file like object with RESP
        information. Any object that provides a read() method will be
        considered to be a file like object.

    :type date: :class:`~obspy.core.utcdatetime.UTCDateTime`
    :param date: Date of interest

    :type station: str
    :param station: Station id

    :type channel: str
    :param channel: Channel id

    :type network: str
    :param network: Network id

    :type locid: str
    :param locid: Location id

    :type units: str
    :param units: Units to return response in. Can be either DEF, DIS, VEL or ACC

    :type debug: bool
    :param debug: Verbose output to stdout. Disabled by default.
   
    :type output: str
    :param output: the style of output to present in data frame ('CS','FAP')
     
    :type spacing: str
    :param spacing: select 'LIN'ear or 'LOG'arithmic spacing of frequency steps

    :rtype: :class:`numpy.ndarray` complex128
    :return: Frequency response from SEED RESP-file of length nfft
    """


    #if isinstance(filename, (str, native_str)):
    if isinstance(filename, (str)):
        with open(filename, 'rb') as fh:
            data = fh.read()
    elif hasattr(filename, 'read'):
        data = filename.read()
    # evalresp needs files with correct line separators depending on OS
    with NamedTemporaryFile() as fh:
        tempfile = fh.name
        fh.write(os.linesep.encode('ascii', 'strict').join(data.splitlines()))
        fh.close()
        # REC - generate the frequency steps
        freqs = np.logspace(M.log10(sfft),M.log10(efft),nfft)     #LOGarithmic (default)
        if spacing == "LIN":
            freqs = np.linspace(sfft,efft,nfft) #LINear
        #print("DEBUG: freqs: %s" % ",".join(str(freqs)))
        start_stage = C.c_int(-1)
        stop_stage = C.c_int(0)
        stdio_flag = C.c_int(0)
        sta = C.create_string_buffer(station.encode('ascii', 'strict'))
        cha = C.create_string_buffer(channel.encode('ascii', 'strict'))
        net = C.create_string_buffer(network.encode('ascii', 'strict'))
        locid = C.create_string_buffer(locid.encode('ascii', 'strict'))
        unts = C.create_string_buffer(units.encode('ascii', 'strict'))
        if debug:
            vbs = C.create_string_buffer(b"-v")
        else:
            vbs = C.create_string_buffer(b"")
        rtyp = C.create_string_buffer(output.encode('ascii','strict'))
        datime = C.create_string_buffer(
            date.format_seed().encode('ascii', 'strict'))
        fn = C.create_string_buffer(tempfile.encode('ascii', 'strict'))
        nfreqs = C.c_int(freqs.shape[0])
        res = clibevresp.evresp(sta, cha, net, locid, datime, unts, fn,
                                freqs, nfreqs, rtyp, vbs, start_stage,
                                stop_stage, stdio_flag, C.c_int(0))
        # res is a struct from C:
        #     struct response {
        #         char station[STALEN];
        #         char network[NETLEN];
        #         char locid[LOCIDLEN];
        #         char channel[CHALEN];
        #         struct evr_complex *rvec;  // complex values - array
        #         int nfreqs;                // number of frequencies
        #         double *freqs;             // list of frequencies - array
        #         struct response *next;
        #     };
        #
        if output == "CS" or output == "FAP":
            try:
                nfreqs, rfreqs, rvec = res[0].nfreqs, res[0].freqs, res[0].rvec
            except ValueError:
                msg = "evalresp failed to calculate a response."
                raise ValueError(msg)
            retlist = None
            f = np.empty(nfreqs, dtype=np.float64)     # frequencies
            if output == "CS":
                h = np.empty(nfreqs, dtype=np.complex128)  # complex array for spectra
                for i in range(nfreqs):
                    f[i] = rfreqs[i]
                    h[i] = rvec[i].real + rvec[i].imag * 1j
                retlist = (f,h)   # return tuple
            else:    # output == FAP :  see evalresp:print_fctns.c for implementation example
                a = np.empty(nfreqs, dtype=np.float64)  # amplitude
                p = np.empty(nfreqs, dtype=np.float64)  # phase
                for i in range(nfreqs):
                    f[i] = rfreqs[i]
                    a[i] = M.sqrt(rvec[i].real * rvec[i].real + rvec[i].imag * rvec[i].imag)
                    p[i] = M.atan2(rvec[i].imag, rvec[i].real + 1.e-200)
                # unwrap phases and convert to degrees
                if (p[0] < 0):
                        p[0] = 2*M.pi + p[0]  # apparently this helps ensure unwrapped phases start causal (range: 0 to 2pi)
                p = np.unwrap(p) * 180 / M.pi
                # return FAP tuple
                retlist = (f,a,p)
            # free up allocated memory
            clibevresp.free_response(res)
            del nfreqs, rfreqs, rvec, res
            return retlist
        else:
            raise ValueError("Unsupported output type: %s" % (output) )
        
        
