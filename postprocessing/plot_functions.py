import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as ctx
import numpy as np
import pandas as pd

def plot_vakindeling(shapefile, output_loc):
    fig, ax = plt.subplots(figsize=(12, 5))
    colors = sns.color_palette('colorblind', n_colors=8)
    colcount = 0
    for count, row in shapefile.iterrows():
        if row.IN_ANALYSE:
            colcount += 1
            try:
                color = colors[colcount]
            except:
                color = colors[0]
                colcount = 0
            ax.plot(*row.geometry.coords.xy, color=color)
            if (count % 2) == 0:
                ax.annotate(text=row['NUMMER'], xy=row.geometry.centroid.coords[:][0],
                            horizontalalignment='center', verticalalignment='bottom', color=color)
            else:
                ax.annotate(text=row['NUMMER'], xy=row.geometry.centroid.coords[:][0],
                            horizontalalignment='center', verticalalignment='top', color=color)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_ylim(bottom=ax.get_ylim()[0] - 1000)
    ctx.add_basemap(ax, source=ctx.providers.Stamen.TonerLite)
    plt.savefig(output_loc, dpi=300, bbox_inches='tight')

def plot_assessment_betas(shapefile, betas, output_dir, year=2025, mechanism_dict = {'StabilityInner':'Stabiliteit', 'Piping':'Piping','Overflow':'Overslag'},close_output=True):
    shapes = {}
    for mech in mechanism_dict.keys():
        subset = betas.loc[betas.mechanism == mech]
        shapes[mech] = shapefile.merge(subset, left_on='NUMMER', right_on='name')

    sns.set_style('whitegrid')
    fig, ax = plt.subplots(nrows=3, figsize=(12, 5))
    for count, axes in enumerate(ax):
        shapes[list(mechanism_dict.keys())[count]].plot(column=str(year-2025), ax=axes, legend=True, vmin=2, vmax=5, cmap='RdYlGn',
                                                    linewidth=4, legend_kwds={'label': r'$\beta$'})
        axes.set_xticklabels([])
        axes.set_yticklabels([])
        axes.set_ylim(bottom=axes.get_ylim()[0] - 1000)

        axes.set_title(mechanism_dict[list(mechanism_dict.keys())[count]])
        ctx.add_basemap(axes, crs=shapes[list(mechanism_dict.keys())[count]].crs, source=ctx.providers.Stamen.TonerLite)
    plt.savefig(output_dir.joinpath('beoordeling_{}_beta.png'.format(year)), dpi=300,
                bbox_inches='tight')
    if close_output:
        plt.close()
def plot_assessment_probabilities(shapefile, probabilities, output_dir, year=2025, mechanism_dict = {'StabilityInner':'Stabiliteit', 'Piping':'Piping','Overflow':'Overslag'},close_output=True):
    shapes = {}
    for mech in mechanism_dict.keys():
        subset = probabilities.loc[probabilities.mechanism==mech]
        shapes[mech] = shapefile.merge(subset,left_on='NUMMER',right_on='name')

    sns.set_style('whitegrid')
    fig,ax = plt.subplots(nrows=3,figsize=(12,5))
    for count, axes in enumerate(ax):
        shapes[list(mechanism_dict.keys())[count]].plot(column=str(year-2025),ax=axes,legend=True,cmap='RdYlGn_r',
                                                    norm=matplotlib.colors.LogNorm(vmin=1e-7,vmax=1e-2), linewidth=4,legend_kwds={'label':'Faalkans','fmt':'{:.0e}'})
        axes.set_xticklabels([])
        axes.set_yticklabels([])
        axes.set_ylim(bottom=axes.get_ylim()[0]-1000)

        axes.set_title(mechanism_dict[list(mechanism_dict.keys())[count]])
        ctx.add_basemap(axes, crs = shapes[list(mechanism_dict.keys())[count]].crs,source=ctx.providers.Stamen.TonerLite)
    plt.savefig(output_dir.joinpath('beoordeling_{}_pf.png'.format(year)), dpi=300,
                bbox_inches='tight')
    if close_output:
        plt.close()


def get_cum_length(section_order, section_lengths):
    sections_stripped = [item.strip('DV') for item in section_order]
    cum_lengths = section_lengths.loc[sections_stripped].cumsum()
    return cum_lengths

def get_cum_costs(section_order,measure_costs):
    return measure_costs.loc[section_order]['LCC'].cumsum()/1e6

def plot_pf_length_cost(vr, dsn, initial_betas, shapefile, output_dir, section_lengths = None, year = 2025,
                                standards = {'Ondergrens': 1./10000, 'Signaleringswaarde': 1./30000},mode = 'Length'):
    # vr and dsn are dictionaries with keys 'traject_probs', 'section_order' and 'optimal_measures'
    year_ind = np.int_(np.argwhere(initial_betas.columns == str(year - 2025))[0][0])
    fig, ax = plt.subplots(figsize=(10, 4))
    if (mode == 'Length') & (section_lengths is not None):
        x_vr = pd.concat([pd.Series([0]), get_cum_length(vr['section_order'], section_lengths)])
        x_dsn = pd.concat([pd.Series([0]), get_cum_length(dsn['section_order'], section_lengths)])
    elif (mode == 'Cost') & ('optimal_measures' in list(vr.keys())):
        x_vr = pd.concat([pd.Series([0]), get_cum_costs(vr['section_order'], vr['optimal_measures'])])
        x_dsn = pd.concat([pd.Series([0]), get_cum_costs(dsn['section_order'], dsn['optimal_measures'])])
    else:
        return 'Error: no section lengths or optimal measures provided'
    ax.plot(x_vr, vr['traject_probs'][:, year_ind], label='Veiligheidsrendement', color='red', marker='.')
    ax.plot(x_dsn, dsn['traject_probs'][:, year_ind], label='Doorsnede-eisen', color='green', marker='.')
    ax.hlines(standards['Ondergrens'], 0, shapefile.MEAS_END.max(), label='Ondergrens', color='k', linestyle='--')

    ax.hlines(standards['Signaleringswaarde'], 0, shapefile.MEAS_END.max(), label='Signaleringswaarde', color='k', linestyle=':')
    # text labels vr:
    for count, section in enumerate(vr['section_order'], 1):
        if (count % 2) == 0:
            ax.text(x_vr.iloc[count], 1e-5, section.strip('DV'), rotation=90, verticalalignment='top', color='red')
        else:
            ax.text(x_vr.iloc[count], 1e-5, section.strip('DV'), rotation=90, verticalalignment='bottom', color='red')

    # text labels dsn:
    for count, section in enumerate(dsn['section_order'], 1):
        if (count % 2) == 0:
            ax.text(x_dsn.iloc[count], 1e-6, section.strip('DV'), rotation=90, verticalalignment='top', color='green')
        else:
            ax.text(x_dsn.iloc[count], 1e-6, section.strip('DV'), rotation=90, verticalalignment='bottom', color='green')
    ax.set_yscale('log')
    if mode == 'Length':
        ax.set_xlim(left=0, right=shapefile.MEAS_END.max())
        ax.set_title('Faalkans i.r.t. versterkte lengte ({})'.format(year))
        ax.set_xlabel('Versterkte lengte in meters')
    elif mode == 'Cost':
        x_max_right = np.max([get_cum_costs(vr['section_order'], vr['optimal_measures']).max(),
                              get_cum_costs(dsn['section_order'], dsn['optimal_measures']).max()])
        ax.set_xlim(left=0, right=x_max_right)
        ax.set_title('Faalkans i.r.t. kosten ({})'.format(year))
        ax.set_xlabel('Kosten in miljoenen euro\'s')
    ax.set_ylim(bottom=1e-7)
    ax.set_ylabel('Trajectfaalkans per jaar')
    ax.legend()
    plt.savefig(output_dir.joinpath('versterkte lengte vs faalkans in {}.png'.format(year)),
                dpi=300, bbox_inches='tight')