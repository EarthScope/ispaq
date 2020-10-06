import pandas as pd
import numpy as np
from . import noise_models
from . import utils
import os



def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

def calculate_PDF(fileDF, sncl, starttime, endtime, concierge):
    # Get the logger from the concierge
    logger = concierge.logger
    

    # For writing to file, before convert the datetime object
    start = starttime.date
    end = endtime.date
            

    if concierge.output == 'csv':
        # Convert datetime for dataframe manipulation
        starttime = starttime.datetime
        endtime = endtime.datetime

    
        # Subset fileDF to only this sncl
        snclFiles = fileDF[fileDF['SNCL'] == sncl]['FILE']
        
        
        
        for snclFile in snclFiles:
            logger.debug('Collecting PSD values from %s' % (snclFile))
    
            psd = pd.read_csv(snclFile, parse_dates=['starttime','endtime'])
            psd.dropna(inplace=True)
    
            # Only include PSDs that are within the time range
            psd=psd[(psd['starttime'] >= starttime) & (psd['endtime'] <= endtime)]
    
            

    elif concierge.output == 'db':
        import sqlite3
        
        # get the values for the sncl and timerange, load into a dataframe
        # Read sqlite query results into a pandas DataFrame
        sqlstarttime = str(starttime).split('.')[0]
        sqlendtime = str(endtime).split('.')[0]
        con = sqlite3.connect(concierge.db_name)
        select_sql = "SELECT * from psd_day WHERE target = '" + sncl +"'"
        if not starttime == "":
            select_sql = select_sql + " AND start >= '" + sqlstarttime + "'"
        if not endtime == "":
            select_sql = select_sql + " AND end <= '" + sqlendtime + "'"
        
        select_sql = select_sql + " AND power != 'nan';"
        logger.debug(select_sql)
        
        psd = pd.read_sql_query(select_sql, con)
        con.close()
    
    # Initiate dataframe to hold hit values
    index = pd.MultiIndex(levels=[[],[]], labels=[[],[]], names=[u'frequency', u'power'])
    pdfDF = pd.DataFrame(columns=['frequency', 'power','hits'], index=index)
        
    # Pre-calculate how many hits each frequency-power bin has for the day
    psd['freqPow'] = list(zip(psd['frequency'], [int(round(i)) for i in psd['power']]))
    freqPows = psd.freqPow.value_counts(sort=False).keys().tolist()
    counts = psd.freqPow.value_counts(sort=False).tolist()
    freqPowCounts = list(zip(freqPows, counts))
            
    # Loop over each frequency-power bin, adding the number of daily hits to the running total
    for freqPow in freqPowCounts:
        freq = freqPow[0][0]
        power = freqPow[0][1]
        count = freqPow[1]
        
        if freqPow[0] in pdfDF.index:
            # We already know of this freq-power combination, add to hit and total counts
            pdfDF['hits'].loc[[freqPow[0]]] += count
    
        else:
            # New frequency-power combination, add to dataframe
            newRow = [freq, power, count]
            ind = len(pdfDF)
            pdfDF.loc[ind] = newRow
            pdfDF.rename(index={ind:freqPow[0]}, inplace=True)


    if pdfDF.empty:
        logger.info('No PSDs found for %s, %s to %s' % (sncl, str(starttime).split('T')[0],str(endtime).split('T')[0]))
        return pdfDF, None, None, None
    
    # Sort the dataframe, mostly for plotting purposes
    pdfDF.sort_values(by=['frequency','power'], inplace=True)
    
    # We used (freq, pow) as the index for ease during construction, but can reset them for the rest of the process
    pdfDF.reset_index(inplace=True,drop=True)
    
    # Set up dataframes for the max, min, modes for plotting later
    modesDF = pd.DataFrame(columns=['Frequency','Power'])
    minsDF = pd.DataFrame(columns=['Frequency','Power']) 
    maxsDF = pd.DataFrame(columns=['Frequency','Power']);
    

    # For each *frequency*, sum up the total hits, as well as min, max, mode values
    for frequency in pdfDF['frequency'].unique():
        # Sum hits for total column
        pdfDF.loc[pdfDF['frequency'] == frequency, 'total'] = sum(pdfDF[pdfDF['frequency'] == frequency]['hits'])
        
        # Find the min, max, mode
        powerInd = pdfDF[pdfDF['frequency'] == frequency]['hits'].idxmax()
        mode = pdfDF.loc[powerInd, 'power']
        modesDF.loc[len(modesDF)] = [frequency, mode]

        indWithHits = pdfDF['hits'][pdfDF['frequency'] == frequency].dropna().index
        values = pdfDF['power'][indWithHits].sort_values().reset_index()
        maxVal = values['power'].iloc[-1]
        minVal = values['power'][0]

        maxsDF.loc[len(maxsDF)] = [frequency, maxVal]
        minsDF.loc[len(minsDF)] = [frequency, minVal]  
    
    pdfDF['percent'] = pdfDF['hits'] / pdfDF['total'] * 100 
    printDF = pdfDF[['frequency', 'power','hits']]  
    sortedDF = printDF.sort_values(['frequency','power'])
    
    if 'text' in concierge.pdf_type:
        
        if concierge.output == "csv":
            logger.info("Write to csv")
            # Write to file
            
            subFolder = '%s/%s/%s/' % (concierge.pdf_dir, sncl.split('.')[0],  sncl.split('.')[1])
            if not os.path.isdir(subFolder):
                logger.info("pdf_dir %s does not exist, creating directory" % subFolder)
                os.makedirs(subFolder)
    
            if str(start) != str(end):      
                filename = sncl + '.' + str(start) + '_' + str(end) + '_PDF.csv'
            else:
                filename = sncl + '.' + str(start) + '_PDF.csv'
            filepath = subFolder + filename
    
            
            logger.info('Writing PDF values to %s' % (filepath))
            
            # start with header, mimicing output from http://service.iris.edu/mustang/noise-pdf/1/query?
            hdr = ('#\n' 
                  '# start=%s\n'
                  '# end=%s\n'
                  '#\n'
                  '#\n' % (starttime,endtime))
        
            
            with open(filepath, mode='w') as f:
                f.write(hdr)
            utils.write_pdf_df(sortedDF, filepath, 'a', sncl, starttime, endtime, concierge, sigfigs=concierge.sigfigs)
        
        elif concierge.output == "db":
            logger.info('Writing PDF values to %s' % concierge.db_name)
            utils.write_pdf_df(sortedDF, "unused", "unused", sncl, starttime, endtime, concierge, sigfigs=concierge.sigfigs)
            
        

    return pdfDF, modesDF, maxsDF, minsDF



def plot_PDF(sncl, starttime, endtime, pdfDF, modesDF, maxsDF, minsDF, concierge):
    import matplotlib.pyplot as plt
    
    # Get the logger from the concierge
    logger = concierge.logger

    # Powers must span the noise models at a minimum
    p1 = int(min(pdfDF['power'].unique())); p2 = int(max(pdfDF['power'].unique()))
    if p1 > -190:
        p1 = -190
    if p2 < -90:
        p2 = -90
        
    
    powers = sorted(range(p1,p2+1), reverse=True)
    freqs = sorted(pdfDF['frequency'].unique(),reverse = True)
    plotDF = pd.DataFrame(0,index=powers,columns=freqs)

    # Create a new dataframe for plotting: rows are powers, columns are periods, value is percent of hits
    nonZeroFreqs=[]
    for power in powers:
        for freq in freqs:
            value = pdfDF[(pdfDF['frequency']==freq) & (pdfDF['power']== power)]['percent'].values
            try:
                plotDF.loc[power,freq] = value[0]
                if value[0] != 0:
                    # Keep track of the frequencies that have hits, for axes limits
                    nonZeroFreqs.append(freq)
            except:
                continue
    
    # Matplotlib imshow takes a list (matrix) of values
    plotList = plotDF.values.tolist()
    
    # Set up plotting -- color map
    cmap = plt.get_cmap('gist_rainbow_r', 3000)
    cmaplist = [cmap(i) for i in range(cmap.N)][100::]  # don't want whole spectrum
    
    # convert the first nchange to fade from white
    nchange = 100
    for i in range(nchange):
        
        first = cmaplist[nchange][0]
        second = cmaplist[nchange][1]
        third = cmaplist[nchange][2]
        scaleFactor = (nchange-1-i)/float(nchange)
        
        df = ((1-first) * scaleFactor) + first
        ds = ((1-second)* scaleFactor) + second
        dt = ((1-third) * scaleFactor) + third
              
        cmaplist[i] = (df, ds, dt, 1)

    cmaplist[0] = (1,1,1,1)
    cmap = cmap.from_list('Custom cmap', cmaplist, cmap.N)

    # Set up plotting -- axis labeling and ticks
    periodPoints = [0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000]
    freqPoints = [1/float(i) for i in periodPoints]
    xfilter = [(i <= freqs[0]) and (i >= freqs[-1]) for i in freqPoints]
    xlabels = [i for (i, v) in zip(freqPoints, xfilter) if v]
    xticks = [find_nearest(freqs, i) for i in xlabels]
    xlabels = [int(1/i)  if i<=1 else 1/i for i in xlabels]     #convert to period, use decimal only if <1s

    yticks = [powers.index(i) for i in list(filter(lambda x: (x % 10 == 0), powers))]
    ylabels = [powers[i] for i in yticks]

    if concierge.plot_include is None:
        concierge.plot_include = "none"
    
    if 'fixed_yaxis_limits' in concierge.plot_include:
        # Need to either extend or truncate the ticks to only range
        # between the default values. 
        
        # first, deal with trimming it down
        if ylabels[0] > -25:
            new_list_a = []
            new_list_b = []
            for a, b in zip(ylabels, yticks):
                if a < -25:
                    new_list_a.append(a)
                    new_list_b.append(b)
            ylabels = new_list_a
            yticks = new_list_b

        if ylabels[-1] < -230:
            new_list_a = []
            new_list_b = []
            for a, b in zip(ylabels, yticks):
                if a > -230:
                    new_list_a.append(a)
                    new_list_b.append(b)
            ylabels = new_list_a
            yticks = new_list_b

        if ylabels[0] < -30:
            while ylabels[0] < -30:
                newTick = yticks[0] - 10
                newLabel = ylabels[0] + 10
                ylabels.insert(0,newLabel)
                yticks.insert(0,newTick)   

        if ylabels[-1] > -220:
            while ylabels[-1] > -220:
                newTick = yticks[-1] + 10
                newLabel = ylabels[-1] - 10
                ylabels.append(newLabel)
                yticks.append(newTick) 
           
            
    
    # Set up plotting -- plot
    height = ylabels[0] - ylabels[-1]
    plt.figure(figsize=( 12, (.055*height + .5) ))
    
    # Plot it up
    plt.imshow(plotList, cmap=cmap,  vmin=0, vmax=30, aspect=.4, interpolation='bilinear')

    # Add mode
    xmodes = [freqs.index(freqPos) for freqPos in modesDF['Frequency'].tolist()]
    ymodes = [powers.index(freqPos) for freqPos in modesDF['Power'].tolist()]
    hmode, = plt.plot(xmodes, ymodes, c='k', linewidth=1, label="mode")
    
    # Add min
    xmins = [freqs.index(freqPos) for freqPos in minsDF['Frequency'].tolist()]
    ymins = [powers.index(freqPos) for freqPos in minsDF['Power'].tolist()]
    hmin, = plt.plot(xmins, ymins, c='r', linewidth=1, label="min")

    # Add max
    xmaxs = [freqs.index(freqPos) for freqPos in maxsDF['Frequency'].tolist()]
    ymaxs = [powers.index(freqPos) for freqPos in maxsDF['Power'].tolist()]
    hmax, = plt.plot(xmaxs, ymaxs, c='b', linewidth=1, label="max")
    
    # Add noise models
    [NHNM, NLNM, freqInd] = noise_models.get_models(freqs,powers)
    plt.plot(freqInd, NHNM, c='dimgrey', linewidth=2)
    plt.plot(freqInd, NLNM, c='dimgrey', linewidth=2)
    
    # Adjust grids, labels, limits, titles, etc
    plt.grid(linestyle=':', linewidth=1)
    plt.xlabel('Period (s)',size=18)
    plt.ylabel(r'Power [$10log_{10}(\frac{m^2/s^4}{hz}$)][dB]',size=18)
    
    plt.xticks(xticks[::-1], xlabels[::-1],size=15)
    plt.yticks(yticks,ylabels,size=15)

    xmin=freqs.index(min(nonZeroFreqs))
    xmax=freqs.index(max(nonZeroFreqs))
    plt.xlim(xmax,xmin)
    plt.ylim(max(yticks)+5,min(yticks)-5)

    title_starttime = str(starttime.datetime)
    title_endtime = str(endtime.datetime)
    plt.title(sncl + '\n'+ title_starttime + " to " + title_endtime, size=18)

    # User has option to include colorbar and/or legend
    if 'colorbar' in concierge.plot_include:
        cb = plt.colorbar(fraction=.02)
        cb.set_label('percent probability',labelpad=-50)
        
    if 'legend' in concierge.plot_include:
        plt.legend([hmax, hmode, hmin],['max','mode','min'], ncol=3, loc='lower left', framealpha=0.8)


    plt.tight_layout()
    
    # Save to file
    subFolder = '%s/%s/%s/' % (concierge.pdf_dir, sncl.split('.')[0],  sncl.split('.')[1])
    if not os.path.isdir(subFolder):
        logger.info("pdf_dir %s does not exist, creating directory" % subFolder)
        os.makedirs(subFolder)
    
    start = starttime.date
    end = endtime.date
    
    if str(start) != str(end):
        filename = sncl + '.' + str(start) + '_' + str(end) + '_PDF.png'
    else:
        filename = sncl + '.' + str(start) + '_PDF.png'
    filepath = subFolder + filename
    
    logger.debug('Saving PDF plot to %s' % (filepath))
    plt.savefig(filepath)


    del(pdfDF)
