import warnings

import contextily as ctx
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import contextily as ctx
import numpy as np
import pandas as pd
import seaborn as sns



def plot_vakindeling(shapefile, output_loc, close_output = True):

    fig, ax = plt.subplots(figsize=(12, 5))
    colors = sns.color_palette("colorblind", n_colors=8)
    colcount = 0

    for count, row in shapefile.iterrows():
        if row.in_analyse:
            colcount += 1
            try:
                color = colors[colcount]
            except:
                color = colors[0]
                colcount = 0
            ax.plot(*row.geometry.coords.xy, color=color)
            if (count % 2) == 0:
                ax.annotate(
                    text=row["vaknaam"],
                    xy=row.geometry.centroid.coords[:][0],
                    horizontalalignment="center",
                    verticalalignment="bottom",
                    color=color,
                )
            else:
                ax.annotate(
                    text=row["vaknaam"],
                    xy=row.geometry.centroid.coords[:][0],
                    horizontalalignment="center",
                    verticalalignment="top",
                    color=color,
                )
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_ylim(bottom=ax.get_ylim()[0] - 1000)
    try:
        ctx.add_basemap(ax, source=ctx.providers.Stamen.TonerLite, crs=shapefile.crs)
    except:
        warnings.warn(
            "Basemap kon niet worden geladen, plot wordt gemaakt zonder achtergrondkaart."
        )
    plt.savefig(output_loc, dpi=300, bbox_inches="tight")
    if close_output:
        plt.close()


def plot_assessment_betas(
    shapefile,
    betas,
    output_dir,
    year=2025,
    mechanism_dict={
        "StabilityInner": "Stabiliteit",
        "Piping": "Piping",
        "Overflow": "Overslag",
    },
    close_output=True,
):
    shapes = {}
    for mech in mechanism_dict.keys():
        subset = betas.loc[betas.mechanism == mech]
        shapes[mech] = shapefile.merge(subset, left_on="vaknaam", right_on="name")

    sns.set_style("whitegrid")
    fig, ax = plt.subplots(nrows=3, figsize=(12, 5))
    for count, axes in enumerate(ax):
        shapes[list(mechanism_dict.keys())[count]].plot(
            column=str(year - 2025),
            ax=axes,
            legend=True,
            vmin=2,
            vmax=5,
            cmap="RdYlGn",
            linewidth=4,
            legend_kwds={"label": r"$\beta$"},
        )
        axes.set_xticklabels([])
        axes.set_yticklabels([])
        axes.set_ylim(bottom=axes.get_ylim()[0] - 1000)

        axes.set_title(mechanism_dict[list(mechanism_dict.keys())[count]])
        ctx.add_basemap(
            axes,
            crs=shapes[list(mechanism_dict.keys())[count]].crs,
            source=ctx.providers.Stamen.TonerLite,
        )
    plt.savefig(
        output_dir.joinpath("beoordeling_{}_beta.png".format(year)),
        dpi=300,
        bbox_inches="tight",
    )
    if close_output:
        plt.close()


def plot_assessment_probabilities(
    shapefile,
    probabilities,
    output_dir,
    year=2025,
    mechanism_dict={
        "StabilityInner": "Stabiliteit",
        "Piping": "Piping",
        "Overflow": "Overslag",
    },
    close_output=True,
):
    shapes = {}
    for mech in mechanism_dict.keys():
        subset = probabilities.loc[probabilities.mechanism == mech]
        shapes[mech] = shapefile.merge(subset, left_on="vaknaam", right_on="name")

    sns.set_style("whitegrid")
    fig, ax = plt.subplots(nrows=3, figsize=(12, 5))
    for count, axes in enumerate(ax):
        shapes[list(mechanism_dict.keys())[count]].plot(
            column=str(year - 2025),
            ax=axes,
            legend=True,
            cmap="RdYlGn_r",
            norm=matplotlib.colors.LogNorm(vmin=1e-7, vmax=1e-2),
            linewidth=4,
            legend_kwds={"label": "Faalkans", "fmt": "{:.0e}"},
        )
        axes.set_xticklabels([])
        axes.set_yticklabels([])
        axes.set_ylim(bottom=axes.get_ylim()[0] - 1000)

        axes.set_title(mechanism_dict[list(mechanism_dict.keys())[count]])
        ctx.add_basemap(
            axes,
            crs=shapes[list(mechanism_dict.keys())[count]].crs,
            source=ctx.providers.Stamen.TonerLite,
        )
    plt.savefig(
        output_dir.joinpath("beoordeling_{}_pf.png".format(year)),
        dpi=300,
        bbox_inches="tight",
    )
    if close_output:
        plt.close()


def get_cum_length(section_order, section_lengths):
    sections_stripped = [item.strip("DV") for item in section_order]
    cum_lengths = section_lengths.loc[sections_stripped].cumsum()
    return cum_lengths

def get_cum_costs(section_order, measure_costs):
    return measure_costs.loc[section_order]["LCC"].cumsum() / 1e6

def plot_pf_length_cost(
    vr,
    dsn,
    initial_betas,
    shapefile,
    output_dir,
    section_lengths=None,
    year=2025,
    standards={"Ondergrens": 1.0 / 10000, "Signaleringswaarde": 1.0 / 30000},
    mode="Length",
    close_output=True,
):
    colors = sns.cubehelix_palette(n_colors=2, start=2.3, rot=1, gamma=1, hue=1.0, light=0.7, dark=0.2)

    # vr and dsn are dictionaries with keys 'traject_probs', 'section_order' and 'optimal_measures'
    year_ind = np.int_(np.argwhere(initial_betas.columns == str(year - 2025))[0][0])
    fig, ax = plt.subplots(figsize=(10, 4))
    if (mode == "Length") & (section_lengths is not None):
        x_vr = pd.concat(
            [pd.Series([0]), get_cum_length(vr["section_order"], section_lengths)]
        )
        x_dsn = pd.concat(
            [pd.Series([0]), get_cum_length(dsn["section_order"], section_lengths)]
        )
    elif (mode == "Cost") & ("optimal_measures" in list(vr.keys())):
        x_vr = pd.concat(
            [pd.Series([0]), get_cum_costs(vr["section_order"], vr["optimal_measures"])]
        )
        x_dsn = pd.concat(
            [
                pd.Series([0]),
                get_cum_costs(dsn["section_order"], dsn["optimal_measures"]),
            ]
        )
    else:
        return "Error: no section lengths or optimal measures provided"
    ax.plot(
        x_vr,
        vr["traject_probs"][:, year_ind],
        label="Veiligheidsrendement",
        color=colors[0],
        marker=".",
    )
    ax.plot(
        x_dsn,
        dsn["traject_probs"][:, year_ind],
        label="Doorsnede-eisen",
        color=colors[1],
        marker=".",
    )
    ax.hlines(
        standards["Ondergrens"],
        0,
        shapefile.m_eind.max(),
        label="Ondergrens",
        color="k",
        linestyle="--",
    )

    ax.hlines(
        standards["Signaleringswaarde"],
        0,
        shapefile.m_eind.max(),
        label="Signaleringswaarde",
        color="k",
        linestyle=":",
    )
    # text labels vr:
    for count, section in enumerate(vr["section_order"], 1):
        if (count % 2) == 0:
            ax.text(x_vr.iloc[count], 1e-5, section.strip('DV'), rotation=90, verticalalignment='top', color=colors[0])
        else:
            ax.text(x_vr.iloc[count], 1e-5, section.strip('DV'), rotation=90, verticalalignment='bottom', color=colors[0])

    # text labels dsn:
    for count, section in enumerate(dsn["section_order"], 1):
        if (count % 2) == 0:
            ax.text(x_dsn.iloc[count], 1e-6, section.strip('DV'), rotation=90, verticalalignment='top', color=colors[1])
        else:
            ax.text(
                x_dsn.iloc[count],
                1e-6,
                section.strip("DV"),
                rotation=90,
                verticalalignment="bottom",
                color=colors[1],
            )
    ax.set_yscale("log")
    if mode == "Length":
        ax.set_xlim(left=0, right=shapefile.m_eind.max())
        ax.set_title("Faalkans i.r.t. versterkte lengte ({})".format(year))
        ax.set_xlabel("Versterkte lengte in meters")
    elif mode == "Cost":
        x_max_right = np.max(
            [
                get_cum_costs(vr["section_order"], vr["optimal_measures"]).max(),
                get_cum_costs(dsn["section_order"], dsn["optimal_measures"]).max(),
            ]
        )
        ax.set_xlim(left=0, right=x_max_right)
        ax.set_title("Faalkans i.r.t. kosten ({})".format(year))
        ax.set_xlabel("Kosten in miljoenen euro's")
    ax.set_ylim(bottom=1e-7)
    ax.set_ylabel("Trajectfaalkans per jaar")
    ax.legend()
    plt.savefig(output_dir.joinpath('versterkte {} vs faalkans in {}.png'.format(mode.lower(), year)),
                dpi=300, bbox_inches='tight')
    if close_output:
        plt.close()

def add_characteristic_columns(result_df):
    #cleaning data
    for count, line in result_df.iterrows():
        try:
            result_df.loc[count,'Section'] = line['Section'].strip('DV')
        except:
            pass
    result_df['In 2045'] = result_df['ID'].str.contains("1", case=False)
    result_df['Stabiliteitsscherm'] = result_df['ID'].str.contains("4|7", case=False)
    result_df['VZG'] = result_df['ID'].str.contains("5", case=False)
    result_df['Diepwand'] = result_df['ID'].str.contains("6", case=False)
    return result_df


def map_of_measures(data, output_dir, include_crest=True, data_type='Optimaal', close_output=True):
    # grondwerk nu
    # grondwerk in 2045
    # VZG, SS en DW
    sns.set_style('whitegrid')
    fig, ax = plt.subplots(figsize=(12, 5))

    data.loc[(data.dberm.values > 0) | (data.dcrest.values > 0)].loc[~data['In 2045']].plot(ax=ax, color='green',
                                                                                            linewidth=5,
                                                                                            label='Grond in 2025')  # ,linestyle='dashed')
    data.loc[(data.dberm.values > 0) | (data.dcrest.values > 0)].loc[data['In 2045']].plot(ax=ax, color='green',
                                                                                           alpha=.5, linewidth=5,
                                                                                           label='Grond in 2045')

    ax.set_xticklabels([])
    ax.set_yticklabels([])

    data.loc[data.VZG].plot(ax=ax, color='r', linestyle='-', linewidth=2, label='VZG')
    data.loc[data.Stabiliteitsscherm].plot(ax=ax, color='b', linestyle='-', linewidth=2, label='Stabiliteitsscherm')
    data.loc[data.Diepwand].plot(ax=ax, color='k', linestyle='-', linewidth=4, label='Diepwand')

    ctx.add_basemap(ax, source=ctx.providers.Stamen.TonerLite)
    ax.legend(bbox_to_anchor=(1.1, .9), fontsize='small')
    ax.set_ylim(bottom=ax.get_ylim()[0] - 1000)
    ax.set_title('Versterkingsmaatregelen - {}'.format(data_type))
    plt.savefig(output_dir.joinpath('versterking_{}.png'.format(data_type)), dpi=300,
                bbox_inches='tight')
    if close_output:
        plt.close()

def map_of_soil_dimensions(data,output_dir,close_output=True):
    sns.set_style('whitegrid')
    fig,ax = plt.subplots(figsize=(12,5),nrows=2)
    data = data.replace(-999.,0)
    data = data.replace(999.,0)
    data['plot_dberm'] = -data.dberm
    dp_list =[]
    m_list = []
    for count, row in data.iterrows():
        if row['In 2045']:
            alpha=0.5
        else:
            alpha=0.8
        ax[0].fill_between(x=[row.m_start,row.m_eind],y1 = [row.dcrest]*2,y2=0,color='blue',alpha=alpha,linestyle=':',linewidth=0)
        ax[1].fill_between(x=[row.m_start,row.m_eind],y1 = [row.plot_dberm]*2,y2=0,color='green',alpha=alpha,linestyle=':',linewidth=0)
        if (count % 8 == 0) or (count == data.shape[0]) or (count == 0):
            dp_list.append(row['VAN_DP'])
            m_list.append(row['m_start'])
    ax[0].fill_between(x=[-100,-99],y1 = [0.1]*2,y2=0,color='blue',alpha=0.5,label='In 2045')
    ax[0].fill_between(x=[-100,-99],y1 = [0.1]*2,y2=0,color='blue',alpha=0.8,label='In 2025')

    # data.plot(kind='area',x='MEAS_START', y='dcrest',ax=ax[0],stacked=False)
    # data.plot(kind='line',x='MEAS_START', y='In 2045',ax=ax[0],stacked=False,linewidth=3)
    ax[0].set_ylabel('Kruinverhoging in meters')
    ax[0].set_xticks([], minor=True)
    # data.plot(kind='area',x='MEAS_START', y='plot_dberm',ax=ax[1],color='red',alpha=0.5,stacked=False)

    ax[0].set_ylim(bottom=0,top=1.5)
    ax[0].set_xlim(left=0,right=data.m_start.max())
    ax[0].set_xticks([], minor=True)
    ax[0].set_xticklabels([])
    ax[0].invert_xaxis()
    ax[0].set_yticks([0.5,1.0,1.5])
    ax[0].legend()

    ax[1].set_xlim(left=0,right=data.m_start.max())
    ax[1].set_xticks([], minor=True)
    ax[1].set_ylabel('Bermverbreding in meters')
    ax[1].invert_xaxis()
    bermticks = [0, -5,-10,-15,-20,-30]
    ax[1].set_ylim(bottom=-35)
    ax[1].set_yticks(bermticks,np.array(bermticks)*-1)
    ax[1].set_xticks(m_list,dp_list)
    fig.subplots_adjust(hspace=-0.)
    plt.savefig(output_dir,dpi=300,bbox_inches='tight')
    if close_output:
        plt.close()

def plot_soil_dim_map(data, output_dir,method= 'Veiligheidsrendement',close_output=True):
    #maatregelen op kaart

    #kruinverhoging:
    sns.set_style('whitegrid')
    fig,ax = plt.subplots(figsize=(12,5),nrows = 2)
    data.replace(-999,0).plot(ax=ax[0],column='dcrest',linewidth=4,cmap='Blues', legend=True, legend_kwds={'label':'kruinverhoging in m',"shrink":.6})
    data.replace(-999,0).plot(ax=ax[1],column='dberm',linewidth=4,cmap='Greens', legend=True, legend_kwds={'label':'bermverbreding in m',"shrink":.6})

    for axes in ax:
        axes.set_xticklabels([])
        axes.set_yticklabels([])
        ctx.add_basemap(axes,source=ctx.providers.Stamen.TonerLite)

    ax[0].set_title('Kruinverhoging')
    ax[1].set_title('Bermverbreding')
    fig.subplots_adjust(hspace=0.0)
    plt.savefig(output_dir.joinpath('{} - kruin en berm.png'.format(method)),dpi=300,bbox_inches='tight')
    if close_output:
        plt.close()


def map_of_measure_cost(data, output_dir, data_type='Optimaal', close_output=True):
    sns.set_style('whitegrid')
    fig, ax = plt.subplots(figsize=(12, 5))
    data['cost per km'] = np.divide(data['LCC'] / 1e6, (data['VAKLENGTE'] / 1e3))
    data.plot(column='cost per km', ax=ax, cmap='RdYlGn_r', legend=True, vmin=0.1, vmax=20, linewidth=2.5,
              legend_kwds={'label': 'M€/km', "shrink": .4})
    ctx.add_basemap(ax, source=ctx.providers.Stamen.TonerLite)
    ax.set_title('Kosten per kilometer - {}'.format(data_type))
    plt.savefig(output_dir.joinpath('kosten_{}.png'.format(data_type)), dpi=300,
                bbox_inches='tight')
    if close_output:
        plt.close()


def map_of_measure_cost_diff(data, output_dir, dif_col, close_output=True):
    # dif_col is the column with the difference in LCC
    sns.set_style('whitegrid')
    fig, ax = plt.subplots(figsize=(12, 5))
    data['cost per km (difference)'] = np.divide(data[dif_col] / 1e6, (data['VAKLENGTE'] / 1e3))

    colors = [(0.0, 'blue'), (0.5, 'green'), (0.75, 'white'), (1.0, 'red')]
    cmap = LinearSegmentedColormap.from_list('custom_colormap', colors)
    data.plot(column='cost per km (difference)', ax=ax, legend=True, vmin=-15, vmax=5, cmap=cmap, linewidth=2.5,
              legend_kwds={'label': 'M€/km', "shrink": .2, 'anchor': (0.1, 0.5)})


    ctx.add_basemap(ax, source=ctx.providers.Stamen.TonerLite)
    ax.set_title('Verschil in kosten per kilometer')
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    plt.savefig(output_dir.joinpath('kosten_verschil.png'), dpi=300, bbox_inches='tight')
    if close_output:
        plt.close()

