import click
from preprocessing.workflows.hydraring_overflow_workflow import overflow_main
from preprocessing.workflows.hydraring_waterlevel_workflow import waterlevel_main
from preprocessing.workflows.generate_vakindeling_workflow import vakindeling_main
from preprocessing.workflows.get_profiles_workflow import main_traject_profiles
from preprocessing.workflows.teenlijn_workflow import main_teenlijn
from preprocessing.workflows.derive_buildings_workflow import main_bebouwing
from preprocessing.workflows.select_profiles_workflow import main_profiel_selectie
from pathlib import Path


@click.group()
def cli():
    pass

@cli.command(
    name="vakindeling", help="Creert een shapefile voor de vakindeling op basis van de ingegeven vakindeling CSV."
)
@click.option("--traject_id",
              type=str,
              nargs=1,
              required=True,
              help="Hier geef je aan om welk traject het gaat. Dit is een string, bijvoorbeeld '38-1'.")
@click.option("--vakindeling_csv",
              type=str,
              nargs=1,
              required=True,
              help="Link naar de CSV met de vakindeling ")
@click.option("--output_folder",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Het pad naar de map waar de uitvoer naartoe wordt geschreven")
@click.option("--traject_shape",
              type=str,
              nargs=1,
              required=False,
              help="Link naar de trajectshapefile. Let op: voer deze alleen in als de gebruikte shapefile afwijkt van"
                   " de shapefile in het NBPW. Als je deze optie niet gebruikt, wordt de shapefile uit het NBPW "
                   "gebruikt.")
@click.option("--flip",
              type=bool,
              nargs=1,
              required=False,
              help="Soms staat de shapefile in het NBPW in de tegenovergestelde richting van je vakindeling. Met andere"
                   "woorden: de vakindeling begint aan de 'verkeerde' kant van de shapefile. Als dit het geval is, kan"
                   "de shapefile worden omgedraaid door deze optie op True te zetten.")
def generate_vakindeling_shape(
    traject_id, vakindeling_csv, output_folder, traject_shape, flip
):
    vakindeling_main(
        traject_id,
        vakindeling_csv,
        Path(output_folder),
        traject_shape,
        flip,
    )

########################################################################################################################
@cli.command(
    name="overflow", help="Generates and evalutes the Hydraring overflow data."
)
@click.option("--work_dir",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Dit is de werkmap, waarin je de resultaten van de overslagsommen wilt uitvoeren. Belangrijk is dat"
                   "deze map voorafgaand aan het runnen van het script al een map met de profielen bevat. Deze map met "
                   "profielen moet de naam 'prfl' hebben. Naast de profielenmap, moet de map leeg zijn")
@click.option("--database_paths",
              type=click.Path(),
              multiple=True,
              required=True,
              help="Link naar de map met de Hydraulische database. "
                   "Omdat er zowel een map voor de situatie huidig, als voor 2100 is,"
                   "moet deze optie twee keer worden opgegeven. Dus:"
                   "--database_paths <pad naar de database voor huidige situatie> --database_paths <pad naar database "
                   "voor de 2100 situatie>")
@click.option("--hydraring_path",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Link naar de map met de Hydraring executable 'MechanismComputation.exe'. Deze executable is meestal"
              " te vinden in: "
                   "'c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236'")
@click.option("--file_name",
              type=str,
              nargs=1,
              required=True,
              help="Link naar de HR_default.csv.")
def generate_and_evaluate_waterlevel_computations(
    work_dir, database_paths, hydraring_path, file_name
):
    overflow_main(
        Path(work_dir),
        list(map(Path, database_paths)),
        Path(hydraring_path),
        file_name,
    )

@cli.command(
    name="waterlevel", help="Generates and evalutes the Hydraring waterlevel data."
)
@click.option("--work_dir",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Dit is de werkmap, waarin je de resultaten van de waterstandsommen wilt uitvoeren. Belangrijk is dat"
                   "deze map leeg is")
@click.option("--database_paths",
              type=click.Path(),
              multiple=True,
              required=True,
              help="Link naar de map met de Hydraulische database. "
                   "Omdat er zowel een map voor de situatie huidig, als voor 2100 is,"
                   "moet deze optie twee keer worden opgegeven. Dus:"
                   "--database_paths <pad naar de database voor huidige situatie> --database_paths <pad naar database "
                   "voor de 2100 situatie>")
@click.option("--hydraring_path",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Link naar de map met de Hydraring executable 'MechanismComputation.exe'. Deze executable is meestal"
              " te vinden in: "
                   "'c:\Program Files (x86)\BOI\Riskeer 21.1.1.2\Application\Standalone\Deltares\HydraRing-20.1.3.10236'")
@click.option("--file_name",
              type=str,
              nargs=1,
              required=True,
              help="Link naar de HR_default.csv.")

def generate_and_evaluate_water_level_computations(
    work_dir, database_paths, hydraring_path, file_name
):
    waterlevel_main(
        Path(work_dir),
        list(map(Path, database_paths)),
        Path(hydraring_path),
        file_name,
    )

################
@cli.command(
    name="genereer_dijkprofielen", help="Voor het afleiden van karakteristieke dijkprofielen af voor een gegeven "
                                        "dijktraject"
)
@click.option("--traject_id",
              type=str,
              nargs=1,
              required=True,
              help="Hier geef je aan om welk traject het gaat. Dit is een string, bijvoorbeeld '38-1'.")
@click.option("--output_folder",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Het pad naar de map waar de uitvoer naartoe wordt geschreven")
@click.option("--traject_shape",
              nargs=1,
              default=False,
              help="Link naar de trajectshapefile. Let op: voer deze alleen in als de gebruikte shapefile afwijkt van"
                   " de shapefile in het NBPW. Als je deze optie niet gebruikt, wordt de shapefile uit het NBPW "
                   "gebruikt.")
@click.option("--flip_traject",
              type=bool,
              nargs=1,
              default=False,
              help="Soms staat de shapefile in het NBPW in de tegenovergestelde richting van je vakindeling. Met andere"
                   "woorden: de vakindeling begint aan de 'verkeerde' kant van de shapefile. Als dit het geval is, kan"
                   "de shapefile worden omgedraaid door deze optie op True te zetten.")
@click.option("--flip_waterkant",
              type=bool,
              nargs=1,
              default=False,
              help="Standaard wordt hier aangenomen dat het water aan de rechterkant van het traject loopt als je de "
                   "nummering van de vakken volgt. Als het water aan de andere linkerkant loopt, moet hier True worden "
                   "ingevuld. Default is False. ")
@click.option("--dx",
                type=int,
                nargs=1,
                default=25,
                help="De afstand tussen de profielen. Optioneel, default is 25 meter.")
@click.option("--voorland_lengte",
                type=int,
                nargs=1,
                default=50,
                help="De lengte van het voorland. Optioneel, default is 50 meter.")
@click.option("--achterland_lengte",
                type=int,
                nargs=1,
                default=75,
                help="De lengte van het voorland. Optioneel, default is 75 meter.")

def obtain_the_AHN_profiles_for_traject(
    traject_id, output_folder, traject_shape, flip_traject, flip_waterkant, dx, voorland_lengte, achterland_lengte
):
    main_traject_profiles(
        str(traject_id),
        Path(output_folder),
        dx,
        voorland_lengte,
        achterland_lengte,
        traject_shape,
        flip_traject,
        flip_waterkant,
    )

@cli.command(name="genereer_teenlijn", help="Voor het afleiden van de teenlijn van een dijktraject"
)
@click.option("--karakteristieke_profielen_map",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je het pad naar de map waar de gegenereerde karakteristieke punten (uit een eerdere stap:"
                   " 'genereer dijkprofielen') zijn opgeslagen")
@click.option("--profiel_info_csv",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Dit is het pad naar de csv met de informatie over de verzamelde profielen (uit een eerdere stap: "
                     "'genereer dijkprofielen'). Deze csv zou traject_profiles.csv moeten heten, tenzij de gebruiker "
                   "de naam heeft aangepast.")
@click.option("--teenlijn_map",
              type=click.Path(),
              nargs=1,
              default=False,
              help="Hier geef je de het pad naar de map waar de teenlijn naartoe moet worden geschreven. De gebruiker"
                   "mag deze map zelf aanmaken, maar als de map niet bestaat, wordt deze automatisch aangemaakt. Het "
                   "uitvoerbestand heet 'teenlijn.geojson'.")

def obtain_inner_toe_line(
    karakteristieke_profielen_map, profiel_info_csv, teenlijn_map
):
    main_teenlijn(
        Path(karakteristieke_profielen_map),
        Path(profiel_info_csv),
        Path(teenlijn_map),
    )



@cli.command(name="tel_gebouwen", help="Voor het afleiden van het aantal gebouwen bij ieder dijkvak vanaf 0 tot 50 meter"
                                       " vanaf de teenlijn landinwaarts"
)
@click.option("--traject_id",
              type=str,
              nargs=1,
              required=True,
              help="Hier geef je aan om welk traject het gaat. Dit is een string, bijvoorbeeld '38-1'")
@click.option("--teenlijn_geojson",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je het pad naar de GeoJSON van de gegenereerde teenlijn. Deze GeoJSON zou teenlijn.geojson"
                   " moeten heten, tenzij de gebruiker de naam heeft aangepast.")
@click.option("--vakindeling_geojson",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je het pad naar de GeoJSON van de gegenereerde vakindeling.")
@click.option("--uitvoer_map",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je de het pad naar de map waar de uitvoer naartoe moet worden geschreven.")
@click.option("--gebouwen_geopackage",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je de het pad naar de geopackage van de BAG. Dit bestand is te downloaden via "
                    "https://service.pdok.nl/lv/bag/atom/bag.xml. Dit is nodig, omdat de BAG het niet toelaat alle "
                   "objecten vanuit het script te downloaden. Het aantal objecten is gelimiteerd tot 1000.")

def tel_alle_gebouwen(
    traject_id, teenlijn_geojson, vakindeling_geojson, uitvoer_map, gebouwen_geopackage
):
    main_bebouwing(
        traject_id,
        Path(teenlijn_geojson),
        Path(vakindeling_geojson),
        Path(uitvoer_map),
        Path(gebouwen_geopackage),
    )

@cli.command(name="selecteer_profiel", help="Selecteer per dijkvak een profiel")


@click.option("--vakindeling_geojson",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je het pad naar de GeoJSON van de gegenereerde vakindeling.")

@click.option("--karakteristieke_profielen_map",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je het pad naar de map waar de gegenereerde karakteristieke punten (uit een eerdere stap:"
                   " 'genereer dijkprofielen') zijn opgeslagen")
@click.option("--profiel_info_csv",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Dit is het pad naar de csv met de informatie over de verzamelde profielen (uit een eerdere stap: "
                     "'genereer dijkprofielen'). Deze csv zou traject_profiles.csv moeten heten, tenzij de gebruiker "
                   "de naam heeft aangepast.")

@click.option("--uitvoer_map",
              type=click.Path(),
              nargs=1,
              required=True,
              help="Hier geef je de het pad naar de map waar de uitvoer naartoe moet worden geschreven.")
@click.option("--invoerbestand",
              type=click.Path(),
              nargs=1,
              default=False,
              help="Het is mogelijk om een invoerbestand op te geven waar voor sommige vakken al profielen zijn ingevoerd.")
@click.option("--selectiemethode",
              type=click.Path(),
              nargs=1,
              default="minimum",
              help="Dit bepaalt de selectiemethode. De opties zijn: minimum (het smalste profiel), gemiddeld (het gemiddelde profiel), en de mediaan")

def selecteer_profiel(
    vakindeling_geojson, karakteristieke_profielen, profiel_info_csv, uitvoer_map, invoerbestand, selectiemethode):
    main_profiel_selectie(
        Path(vakindeling_geojson),
        Path(karakteristieke_profielen),
        Path(profiel_info_csv),
        Path(uitvoer_map),
        Path(invoerbestand),
        selectiemethode)


if __name__ == "__main__":
    cli()
