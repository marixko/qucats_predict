import itertools
from collections import OrderedDict 


aper = 'PStotal'
specz = 'Z'

feat_broad = ['u', 'g', 'r', 'i', 'z']
broad = [item+'_'+aper for item in feat_broad]
feat_narrow = ['J0378', 'J0395', 'J0410', 'J0430', 'J0515', 'J0660', 'J0861']
narrow = [item+'_'+aper for item in feat_narrow]
splus = broad + narrow
wise_flux = ['FW1', 'FW2']
wise = ['W1', 'W2']
galex = ['FUVmag', 'NUVmag']

error_splus = ['e_'+item for item in splus]
error_wise = [item+'_ERR' for item in wise]
error_galex = ['e_'+item for item in galex]

def list_feat(broad=None, narrow=None, wise=None, galex=None):
    list_feat = []
    features = create_features()
    if broad:
        for key in features['splus']['broad']:
            list_feat.append(key)
    if narrow:
        for key in features['splus']['narrow']:
            list_feat.append(key)
    if wise:
        for key in features['wise']:
            list_feat.append(key)
    if galex:
        for key in features['galex']:
            list_feat.append(key)
    return list_feat

def create_features():
    
    features = OrderedDict()
    features = {'wise': None,
                'splus': {'broad': None,
                          'narrow': None},
                'galex': None}

    features['wise'] = {'W1': 34000,
                        'W2': 46000}

    features['galex'] = {'FUVmag': 1528,
                         'NUVmag': 2310}

    features['splus']['broad'] = {'u': 3536,
                                  'g': 4751,
                                  'r': 6258,
                                  'i': 7690,
                                  'z': 8831}

    features['splus']['narrow'] = {'J0378': 3770,
                                   'J0395': 3940,
                                   'J0410': 4094,
                                   'J0430': 4292,
                                   'J0515': 5133,
                                   'J0660': 6614,
                                   'J0861': 8611}
    
    features['splus']['broad'] = {k+'_'+aper:v for k,v in features['splus']['broad'].items()}
    features['splus']['narrow'] = {k+'_'+aper:v for k,v in features['splus']['narrow'].items()}
    
    return features

def create_colors(broad, narrow, wise, galex):
    
    colors = []
    ref_key = 'r' + '_' + aper
    ref = 6258
    
    list_features = []
    features = create_features()

    if broad == True:
        list_features = list_features+list(features['splus']['broad'])
    if narrow == True:
        list_features = list_features+list(features['splus']['narrow'])
    if wise == True:
        list_features = list_features+list(features['wise'])
    if galex == True:
        list_features = list_features+list(features['galex'])

    try: list_features.remove(ref_key)
    except: pass

    for key in list_features:
        
        try:
            if features['splus']['broad'][key] < ref:
                colors.append(key+'-'+ref_key)
            else:
                colors.append(ref_key+'-'+key)
        except: None
        
        try:
            if features['splus']['narrow'][key] < ref:
                colors.append(key+'-'+ref_key)
            else:
                colors.append(ref_key+'-'+key)
        except: None
        
        try:
            if features['wise'][key] < ref:
                colors.append(key+'-'+ref_key)
            else:
                colors.append(ref_key+'-'+key)
        except: None
        
        try:
            if features['galex'][key] < ref:
                colors.append(key+'-'+ref_key)
            else:
                colors.append(ref_key+'-'+key)
        except: None

    return colors

def calculate_colors(data, broad, narrow, wise, galex):
    
    colors = create_colors(broad=broad, narrow=narrow, wise=wise, galex=galex)
    for c in colors:
        aux = c.split('-')
        data[c] = data[aux[0]] - data[aux[1]]
    
    return data

def create_ratio(broad,narrow, wise, galex):
    
    feat_mag = list_feat(broad=broad, narrow=narrow, wise=wise, galex=galex)
    feat_ratios = []
    ratios = list(itertools.combinations(feat_mag, 2))
    
    for col in ratios:
        name = col[0] + '/' + col[1]
        feat_ratios.append(name)
    
    return feat_ratios

def calculate_ratio(data, broad, narrow, wise, galex):
    
    feat_mag = list_feat(broad=broad, narrow=narrow, wise=wise, galex=galex)
    ratio = list(itertools.combinations(feat_mag, 2))
    feat_ratio = []
    
    for col in ratio:
        name = col[0] + '/' + col[1]
        feat_ratio.append(name)
        data[name] = data[col[0]] / data[col[1]]
        data[name].replace({1: 99}, inplace=True)
    
    return data


def convert_f64_to_f32(df, exclude_columns=["RA", "DEC"]):
    """
    Convert all float64 columns to float32, excluding specified columns.

    Parameters:
    - df: pandas DataFrame to process.
    - exclude_columns: list of column names to exclude from conversion.

    Returns:
    - DataFrame with float64 columns converted to float32, except excluded columns.
    """
    if exclude_columns is None:
        exclude_columns = []

    for column in df.select_dtypes(include=['float64']).columns:
        if column not in exclude_columns:
            df[column] = df[column].astype('float32')

    return df