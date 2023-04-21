# Preprocessing #

## Algemene workflow
* Doel van de preprocessing is het vertalen van beoordelingsinformatie naar invoer voor de VRTOOL.
* Aanvullend is extra informatie nodig, maar dat wordt zoveel mogelijk uit landsbreed beschikbare gegevens gehaald (bijv. Basisadministratie Gebouwen, AHN en NBPW)

Eindpunt van de workflow is dat een SQLite database wordt gecreerd waarmee de VRTOOL kan worden gedraaid. Deze bevat alle benodigde invoer.

Globaal heeft de workflow 3 stappen:
1. Het definieren van een vakindeling voor het dijktraject.
2. Het vullen van de tabellen met de benodigde informatie voor het doorrekenen van mechanismen.
3. Het vullen van dijkvakspecifieke eigenschappen zoals bebouwing, profiel en beschikbare dijkversterkingsmaatregelen.


## Stap 1: het definieren van een vakindeling
Het definieren van een vakindeling gebeurt op basis van een ingevuld *.csv bestand. 

[Beschrijf de workflow verder]


## Stap 2: het vullen van mechanisme-informatie

### Informatie voor overslag en waterstand
* Vul HR_input.csv in
* Optie 1 is om per dijkvak al 1 rij toe te voegen.
* Optie 2 is om een aparte workflow te gebruiken om per dijkvak de maatgevende berekening te selecteren. Dit behoeft andere invoer.

Na het vullen van HR_input.csv kunnen met Hydra-Ring berekeningen worden uitgevoerd voor overslag en waterstand, voor 2023 en 2100.
Dit gebeurt met de workflow [hier een linkje]

Tot slot worden de resultaten gevalideerd, en worden deze weggeschreven naar de opgegeven SQLite database.

### Informatie voor piping


### Informatie voor stabiliteit

## Stap 3: het vullen van dijkvakspecifieke informatie
* Teenlijn
* Huizen
* Profielen
* Maatregelen
