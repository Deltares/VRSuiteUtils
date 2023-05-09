import matplotlib.pyplot as plt
import seaborn as sns
import contextily as ctx
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

