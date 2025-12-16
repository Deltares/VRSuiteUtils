# To build this docker (from the root checkout) run:
# `docker build -t vrtool_utils_externals -f .devcontainer/externals.Dockerfile`

FROM ubuntu:latest

ARG SRC_ROOT="/usr/src"

WORKDIR $SRC_ROOT/app
COPY externals $SRC_ROOT/test_externals
RUN chmod a+x "${SRC_ROOT}/test_externals/HydraRing-23.1.1"


# Define the endpoint
CMD [ "/bin/bash" ]