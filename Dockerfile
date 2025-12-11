# To build this docker run:
# `docker build -t vrtool-utils`
# To run this docker:
# `docker run -it 
# -v <path_to_mount>:.
# vrtool-utils {<command>}`
# This will mount the local externals directory to /app/externals in the container.
FROM python:3.12

RUN apt-get update

# Copy the directories with the local vrtool.
WORKDIR /app
COPY README.md pyproject.toml /app/
COPY preprocessing /app/preprocessing
COPY postprocessing /app/postprocessing

# Install koswat and its dependencies.
RUN pip install /app

# Set the entrypoint to run vrtool as a module.
ENTRYPOINT ["python", "-m"]
