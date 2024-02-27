from numpy import asarray, abs


def find_nearest_idx(array, value):
    '''General function to find the nearest idx of an item in a list
    https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array'''
    array = asarray(array)
    idx = (abs(array - value)).argmin()
    return idx


def Odds(x, cdf_object, zphot):
    '''arXiv 9811189, eq. 17
    Also calculated as the integral of the PDF between z_peak +/- 0.02'''
    plus = cdf_object[find_nearest_idx(x, zphot+0.1)]
    minus = cdf_object[find_nearest_idx(x, zphot-0.1)]
    return plus - minus


def Q(alpha:int, x, cdf_object, lower=True):
    '''Calculate the alpha% credible interval.'''
    q_val = (1 - (alpha/100)) / 2
    if lower: return x[find_nearest_idx(cdf_object, q_val)]
    else: return x[find_nearest_idx(cdf_object, 1-q_val)]
