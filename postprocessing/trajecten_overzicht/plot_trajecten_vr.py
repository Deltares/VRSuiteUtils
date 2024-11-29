import geopandas as gpd
from owslib.wfs import WebFeatureService
import matplotlib.pyplot as plt
import contextily as ctx
import pandas as pd
import seaborn as sns
import datetime

wfs_nbpw = WebFeatureService(
    url="https://waterveiligheidsportaal.nl/geoserver/nbpw/ows/wfs",
    version="1.1.0",
)
NBPW2 = gpd.read_file(
    wfs_nbpw.getfeature("nbpw:dijktrajecten", outputFormat="json")
)
vr_data = pd.read_csv(r'postprocessing/trajecten_overzicht/trajecten.csv')

#merge vr_data with NBPW2
NBPW2 = NBPW2.merge(vr_data, left_on='TRAJECT_ID', right_on='TRAJECT_ID', how='left')

fig, ax = plt.subplots(figsize=(15,10))
colors = sns.color_palette("Set2", 10)
NBPW2.loc[NBPW2.Type == 'Dijk'].plot(ax=ax,color='darkgray', linewidth=1, label = 'Dijktrajecten')
NBPW2.loc[NBPW2.Type == 'Duin'].plot(ax=ax,color='gray', linewidth=1, label = 'Duintrajecten')
NBPW2.set_index('TRAJECT_ID',inplace=True)
lengtes = {}
for count, status in enumerate(NBPW2.Status.dropna().unique()):
    NBPW2.loc[NBPW2.Status==status].plot(ax=ax,color=colors[count], linewidth=2, label = status)
    NBPW2.loc[NBPW2.Status==status].apply(lambda x: ax.annotate(text=x.name, xy=x.geometry.centroid.coords[0], ha='center',fontsize='x-small'), axis=1)
    lengtes[status] = NBPW2.loc[NBPW2.Status==status].lengte.sum()
lengtes['Totaal dijken'] = NBPW2.loc[NBPW2.Type == 'Dijk'].lengte.sum()

waterschappen = NBPW2.loc[~NBPW2.Status.isna()].waterschap.unique()
lengtes['In project'] = NBPW2.loc[NBPW2.waterschap.isin(waterschappen)].lengte.sum()

#TODO make a bar chart with totaal dijken and in project as overlapping bars. Then overlay it with a narrow bar where 'In versterking', 'SAFE', 'Fase 1' and 'Gepland' are shown
#put it in the left top corner of the plot
lengtes = pd.DataFrame(lengtes,index=[0])
print(lengtes)
# ax.bar(x=0, height=lengtes.loc['Totaal dijken','lengte'], width=0.5, color='darkgray', label='Totaal dijken')
# ax.bar(x=0.5, height=lengtes.loc['In project','lengte'], width=0.5, color='lightgray', label='In project')

ctx.add_basemap(ax=ax, source=ctx.providers.nlmaps.grijs
                , crs='EPSG:28992')
ax.legend()
ax.set_xticklabels([])
ax.set_yticklabels([])
ax.set_xticks([])
ax.set_yticks([])
#get date
now = datetime.datetime.now()
plt.title(f"Trajecten veiligheidsrendement \n{now.strftime('%d-%m-%Y')}")

plt.savefig(r'postprocessing\trajecten_overzicht\TrajectenVeiligheidsrendement_' + now.strftime("%Y_%m_%d")  + '.png',bbox_inches='tight',dpi=300)
