
## Junk script for initial testing of rpy2.  This file will likely get deleted after testing is done.

try:
    import rpy2.robjects as robjects
    r = robjects.r
except Exception, e:
    status = 'ERROR'
    error_text = str(e)
    
pi = r['pi']

print pi[0]