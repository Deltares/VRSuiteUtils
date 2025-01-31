# VRSuiteUtils #

This repository contains preprocessing tools to process input from a WBI assessment and openly available data to generate input databases for the [VRTOOL](https://github.com/Deltares/Veiligheidsrendement). Additionally it contains tools to process and analyze results from the VRTOOL. Further guidelines can be found [here](https://deltares-research.github.io/VrtoolDocumentation/).

The current version that this repository pertains to is VRTOOL v1.0.1

## How do I get set up? ##
Installation instructions are found [here](https://deltares-research.github.io/VrtoolDocumentation/Installaties/index.html) for general users. 

Of course it is also possible to download the repository and run it from the environment as specified in the .yml and .toml files.
Use of [miniforge](https://conda-forge.org/miniforge/) is advised for this. Then run:

```
conda env create -f .config\environment.yml -p .env/
conda activate .env/
poetry install
```
> IMPORTANT! If the installation fails because of the `vrtool` dependency (or any related like `peewee`) try installing through pip (`pip install .`) and then installing again through poetry `poetry install`

## Contribution and usage ##
VRSuiteUtils is shared with the MIT license. 

If you want to contribute contact the repository owner. Any contribution should be testable and useful for more than just your own case study, otherwise you should keep it locally or generalize first. Contributions can be shared using a Pull Request that will be reviewed by the repository owners.

## Who do I talk to? ##

For questions about the repository contact Wouter Jan Klerk or Stephan Rikkert.

wouterjan.klerk@deltares.nl

stephan.rikkert@deltares.nl
