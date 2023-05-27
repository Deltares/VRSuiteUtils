# Veiligheidsrendement Tools #

This repository contains tools to process input from a WBI assessment to input for the VRTOOL, which can be used to apply the veiligheidsrendementmethode to determine optimized configurations of dike reinforcements. Additionally it contains tools to process and analyze results from the VRTOOL

## What is this repository for?

* The current version that this repository pertains to is VRTOOL v0.1

## How do I get set up? ##

* Download the repository and run it from the environment as specified in the .yml and .toml files.

* Using Anaconda (or miniconda):
```
conda env create -f .config\environment.yml -p .env
conda activate .env
poetry install
```
> IMPORTANT! If the installation fails because of the `vrtool` dependency (or any related like `peewee`) try installing through pip (`pip install .`) and then installing again through poetry `poetry install`

## Contribution guidelines ##

If you want to contribute contact the repository owner. Any contribution should be testable and useful for more than just your own case study, otherwise you should keep it locally or generalize first.

## Who do I talk to? ##

For questions about the repository contact Wouter Jan Klerk or Stephan Rikkert.

wouterjan.klerk@deltares.nl

stephan.rikkert@deltares.nl
