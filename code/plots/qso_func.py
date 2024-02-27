import os
from functools import reduce

import numpy as np
import pandas as pd
from astropy.table import Table
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


plt.rcParams["font.size"] = 22
plt.rcParams["ytick.minor.visible"] = True
plt.rcParams["xtick.minor.visible"] = True


def match_tables(field):
    '''Usar pra pegar dados.'''
    
    path_z = '/storage/splus/Catalogues/VACs/qso_z/iDR4'
    path_sqg = '/storage/splus/Catalogues/VACs/sqg/iDR4'
    path_dual = '/storage/splus/Catalogues/iDR4/dual'
    
    ### PHOTO-ZS ###
    z = pd.read_csv(os.path.join(path_z, field+'_QSOz_VAC.csv'),
                    #usecols=['ID', 'RA', 'DEC', 'z_rf', 'z_bmdn_peak', 'z_flex_peak', 'z_mean', 'z_std', 'n_peaks_bmdn'],
                    #usecols=['ID', 'RA', 'DEC', 'z_mean', 'z_std'],
                    usecols=['ID', 'RA', 'DEC', 'z_rf', 'z_bmdn_peak', 'z_flex_peak', 'z_mean'],
                    dtype={'n_peaks_bmdn': np.uint8})
    
    ### CLASSIFICAÇÃO ###
    clas = Table.read(os.path.join(path_sqg, field+'.fits'), format='fits').to_pandas()
    clas = clas[['ID', 'CLASS', 'PROB_QSO', 'PROB_STAR', 'PROB_GAL']]#, 'model_flag']]
    
    # queries
    clas = clas[clas['CLASS'] == 0].drop('CLASS', axis=1)
    #clas = clas[clas['PROB_QSO'] > 0.8].drop('CLASS', axis=1)
    
    # tipos + decode no ID para match
    clas = clas.astype({'PROB_QSO': np.float32, 'PROB_STAR': np.float32, 'PROB_GAL': np.float32})
    clas['ID'] = clas['ID'].str.decode('utf-8')
    
    ### MAGNITUDES ###
    
    bands = {'u': 'U', 'J0378': 'F378', 'J0395': 'F395', 'J0410': 'F410', 'J0430': 'F430', 'g': 'G',
             'J0515': 'F515', 'r': 'R', 'J0660': 'F660', 'i': 'I', 'J0861': 'F861', 'z': 'Z'}
    mags_dfs = []
    for band, name in bands.items():
        mag = Table.read(os.path.join(path_dual, field+f'_{name}_dual.fits'), format='fits').to_pandas()
        #mag = mag[['ID', f'{band}_PStotal', f'e_{band}_PStotal', f'SEX_FLAGS_{band}']]
        mag = mag[['ID', f'{band}_PStotal']]
        
        # tipos + decode no ID para match
        #mag = mag.astype({f'SEX_FLAGS_{band}': np.uint8})
        mag['ID'] = mag['ID'].str.decode('utf-8')
    
    # juntar todas as bandas
        mags_dfs.append(mag)
    mags = reduce(lambda left, right: pd.merge(left, right, on=['ID'], how='outer'), mags_dfs)
    
    # queries
    mags = mags[mags['r_PStotal'] < 22]
    #mags = mags.query('&'.join([f'{b}!=99' for b in bands]))
    
    ### S-PLUS COLUMNS ###
    pf = Table.read(os.path.join(path_dual, field+'_detection_dual.fits'), format='fits').to_pandas()
    pf = pf[['ID', 'Field', 'SEX_FLAGS_DET']]
    
    # queries
    # pf = pf[pf['SEX_FLAGS_DET'] == 0].drop('SEX_FLAGS_DET', axis=1)
    pf = pf.astype({'SEX_FLAGS_DET': np.uint8})
    
    # tipos + decode no ID para match
    pf['ID'] = pf['ID'].str.decode('utf-8')
    pf['Field'] = pf['Field'].str.decode('utf-8')
    
    
    ### MATCH ALL TABLES ###    
    match = pd.merge(z, clas, on='ID')
    match = pd.merge(match, mags, on='ID')
    match = pd.merge(match, pf, on='ID')

    return match


def match_tables_paper(field):
    '''Não mexer, configurada para os plots do paper.'''
    
    path_z = '/storage/splus/Catalogues/VACs/qso_z/iDR4'
    path_sqg = '/storage/splus/Catalogues/VACs/sqg/iDR4'
    path_dual = '/storage/splus/Catalogues/iDR4/dual'
    
    ### PHOTO-ZS ###
    z = pd.read_csv(os.path.join(path_z, field+'_QSOz_VAC.csv'),
                    usecols=['ID', 'RA', 'DEC', 'z_rf', 'z_bmdn_peak', 'z_flex_peak', 'z_mean', 'z_std', 'n_peaks_bmdn'],
                    dtype={'n_peaks_bmdn': np.uint8})
    
    ### CLASSIFICAÇÃO ###
    clas = Table.read(os.path.join(path_sqg, field+'.fits'), format='fits').to_pandas()
    clas = clas[['ID', 'CLASS', 'PROB_QSO', 'PROB_STAR', 'PROB_GAL']]
    
    # queries
    clas = clas[clas['CLASS'] == 0].drop('CLASS', axis=1)
    
    # tipos + decode no ID para match
    clas = clas.astype({'PROB_QSO': np.float32, 'PROB_STAR': np.float32, 'PROB_GAL': np.float32})
    clas['ID'] = clas['ID'].str.decode('utf-8')
    
    ### MAGNITUDES ###
    
    bands = {'u': 'U', 'J0378': 'F378', 'J0395': 'F395', 'J0410': 'F410', 'J0430': 'F430', 'g': 'G',
             'J0515': 'F515', 'r': 'R', 'J0660': 'F660', 'i': 'I', 'J0861': 'F861', 'z': 'Z'}
    mags_dfs = []
    for band, name in bands.items():
        mag = Table.read(os.path.join(path_dual, field+f'_{name}_dual.fits'), format='fits').to_pandas()
        mag = mag[['ID', f'{band}_PStotal']]
        
        # tipos + decode no ID para match
        mag['ID'] = mag['ID'].str.decode('utf-8')
    
    # juntar todas as bandas
        mags_dfs.append(mag)
    mags = reduce(lambda left, right: pd.merge(left, right, on=['ID'], how='outer'), mags_dfs)
    
    # queries
    mags = mags[mags['r_PStotal'] < 21.3]
    
    ### S-PLUS COLUMNS ###
    pf = Table.read(os.path.join(path_dual, field+'_detection_dual.fits'), format='fits').to_pandas()
    pf = pf[['ID', 'Field', 'SEX_FLAGS_DET']]
    
    # queries
    pf = pf[pf['SEX_FLAGS_DET'] == 0].drop('SEX_FLAGS_DET', axis=1)
    
    # tipos + decode no ID para match
    pf['ID'] = pf['ID'].str.decode('utf-8')
    pf['Field'] = pf['Field'].str.decode('utf-8')
    
    ### MATCH ALL TABLES ###    
    match = pd.merge(z, clas, on='ID')
    match = pd.merge(match, mags, on='ID')
    match = pd.merge(match, pf, on='ID')

    return match


def density_map(data, x:list, y:str, n_fields:int, per_area=True, save=False):

    area = 1.4 * 1.4 * n_fields

    fig = plt.figure(figsize=(27, 5))
    gs = gridspec.GridSpec(nrows=2, ncols=5, figure=fig,
                           width_ratios=[1, 1, 1, 1, 1/15], height_ratios=[1, 3],
                           wspace=0.07, hspace=0.06)

    cmap = mpl.cm.get_cmap("jet", 8).copy()
    cmap.set_under(color='black')
    
    y = data[y].to_numpy()
    yedges = np.arange(np.min(y), np.max(y)+0.1, 0.1)
    half_bins = np.arange(0.05, 5.05, 0.1)
    
    ax1d_top = fig.add_subplot(gs[0, 0])
    axes1d = [ax1d_top] + [fig.add_subplot(gs[0, i], sharey=ax1d_top) for i in range(1, 4)]
    ax2d_bottom = fig.add_subplot(gs[1, 0])
    axes2d = [ax2d_bottom] + [fig.add_subplot(gs[1, i], sharey=ax2d_bottom) for i in range(1, 4)]
    
    
    for method, i, name  in zip(x, [0, 1, 2, 3], ["RF", "BMDN", "FlexCoDE", "Average"]):
        
        x = data[method].to_numpy()
        xedges = np.arange(0, 5.1, 0.1)
        h, xedges, yedges = np.histogram2d(x, y, bins=[xedges, yedges])
        
        ax1d = axes1d[i]
        ax2d = axes2d[i]

        if per_area:
            im = ax2d.imshow(h.T/area, origin='lower',
                    extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
                    aspect='auto', interpolation='nearest', cmap=cmap, vmin=1e-8)
        else:
            im = ax2d.imshow(h.T, origin='lower',
                    extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
                    aspect='auto', interpolation='nearest', cmap=cmap, vmin=1e-8)
        ax2d.set_xlabel(r"$z_{phot}$")
        
        
        n, _ = np.histogram(data[method], bins=np.arange(0, 5.1, 0.1))
        ax1d.plot(half_bins, n/area, '-k', lw=1)
        ax1d.scatter(half_bins, n/area, color="black", s=10)
        ax1d.set_xticks([])
        ax1d.set_yticks([10, 25])

        ax2d.text(0.95, 0.08, name, horizontalalignment='right', verticalalignment='center',
                     transform = ax2d.transAxes, color="white")
        ax2d.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5])

        ax1d.tick_params(axis='y', which='major')
        ax2d.tick_params(axis='both', which='major')

        if i == 0:
            ax2d.set_ylabel(r"$r$")
            ax2d.set_yticks(list(range(17, 22)))
            ax1d.set_ylabel(r"N/deg$^2$")
        else:
            axes1d[i].tick_params(axis='y', which='both', left=False, labelleft=False)
            axes2d[i].tick_params(axis='y', which='both', left=False, labelleft=False)
    
    cbar_ax = fig.add_subplot(gs[:, 4])
    cb = plt.colorbar(im, cax=cbar_ax, pad=0.001)
    if per_area:
        cb.set_label(r'Candidates per deg$^2$')
    else:
        cb.formatter.set_powerlimits((0, 0))
    
    if save:
        plt.savefig('density_map.png',  bbox_inches='tight', facecolor='white', dpi=300)
        plt.savefig('density_map.eps',  bbox_inches='tight', facecolor='white', format='eps')
    plt.show()
    plt.close()
