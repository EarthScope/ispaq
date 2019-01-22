# The NHNM and NLNM from Peterson, 1993
import math

def get_models(frequencies,powers):
    periods = [1/f for f in frequencies]
    NHNM = []
    NLNM = []
    PERIODS = []    # the indices corresponding to periods within the defined models
    

    # NHNM
    Ph = [0.10, 0.22, 0.32, 0.80, 3.80, 4.60, 6.30, 7.90, 15.40, 20.00, 354.80, 100000.00]
    Ah = [-108.73, -150.34, -122.31, -116.85, -108.48, -74.66, 0.66, -93.37, 73.54, -151.52, -206.66]
    Bh = [-17.23, -80.50, -23.87, 32.51, 18.08, -32.95, -127.18, -22.42, -162.98, 10.01, 31.63]

    
    #for i in len(A):
    #    nhnm = A[i] + B[i] * math.log(P[i], 10)
    #    NHNM.append(nhnm)



    # NLNM
    Pl = [0.10, 0.17, 0.40, 0.80, 1.24, 2.40, 4.30, 5.00, 6.00, 10.00, 12.00, 15.60, 21.90, 
          31.60, 45.00, 70.00, 101.00, 154.00, 328.00, 600.00, 10000.00, 100000.00]
    Al = [-162.36, -166.7, -170.00, -166.40, -168.60, -159.98, -141.10, -71.36, -97.26, 
          -132.18, -205.27, -37.65, -114.37, -160.58, -187.50, -216.47, -185.00, -168.34, 
          -217.43, -258.28, -346.88]
    Bl = [5.64, 0.00, -8.30, 28.90, 52.48, 29.81, 0.00, -99.77, -66.49, -31.57, 36.16, 
          -104.33, -47.10, -16.28, 0.00, 15.70, 0.00, -7.61, 11.90, 26.60, 48.75]
    
    
    pInd=0
    for period in periods:
        # find where this period lies in the list of noise model periods
        try:
            highInd = [i for i, x in enumerate([period > Ph][0]) if x][-1]
            lowInd = [i for i, x in enumerate([period > Pl][0]) if x][-1]

        except:
            pInd += 1
            continue
        
        nhnm = Ah[highInd] + Bh[highInd] * math.log(period, 10)    # power value
        nhnmInd = [i for i, x in enumerate(powers) if x == int(nhnm)][0]    # index for that power
        
        nlnm = Al[lowInd] + Bl[lowInd] * math.log(period, 10)
        nlnmInd = [i for i, x in enumerate(powers) if x == int(nlnm)][0] 
            
        NHNM.append(nhnmInd)
        NLNM.append(nlnmInd)
        PERIODS.append(pInd)
            
        pInd += 1
        
    return NHNM, NLNM, PERIODS    
