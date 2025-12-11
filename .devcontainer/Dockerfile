FROM ghcr.io/prefix-dev/pixi:latest AS pixi-base
# This image overlay was the best way I found to run (linux) .Net applications within
# a miniforge container.

ARG SRC_ROOT="/usr/src"
# Set PIXI_HOME to a location inside the source root
ENV PIXI_HOME=$SRC_ROOT/.pixi

# This location needs to be mounted with your vrtool checkout:
# -v {your_vrtool_checkout_dir}:/usr/src/app
WORKDIR $SRC_ROOT/app

# This apparently is necessary for matplotlib to work properly
RUN apt-get update 
RUN apt-get install -y tcl tk

# Define the endpoint
CMD [ "/bin/bash" ]