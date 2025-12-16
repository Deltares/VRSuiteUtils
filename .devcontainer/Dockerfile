# To build this docker (from the root checkout) run:
# `docker build -t vrtool_externals_dev .devcontainer`
# To run the docker for pytest:
# `docker run -v {your_vrtool_checkout_dir}:/usr/src/app/ -v {vrtool_env_dir}:/usr/src/.env -t vrtool_externals_dev`
# `pixi install -e dev`
# `pixi run -e dev pytest -m {your_pytest_arguments}`

FROM containers.deltares.nl/gfs-dev/vrtool_utils_externals:latest AS vrtool_utils_externals-env
FROM ghcr.io/prefix-dev/pixi:latest AS pixi-base
# Use the pixi base image
ARG SRC_ROOT="/usr/src"
# Set PIXI_HOME to a location inside the source root
ENV PIXI_HOME=$SRC_ROOT/.pixi

# This location needs to be mounted with your vrtool checkout:
# -v {your_vrtool_checkout_dir}:/usr/src/app
WORKDIR $SRC_ROOT/app

COPY --from=vrtool_utils_externals-env $SRC_ROOT/test_externals ${SRC_EXTERNALS}

# Define the endpoint
CMD [ "/bin/bash" ]