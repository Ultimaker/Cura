FROM ultimaker/cura-build-environment:3.2

# Environment vars for easy configuration
ENV CURA_BRANCH=master
ENV URANIUM_BRANCH=$CURA_BRANCH
ENV CURA_BENV_GIT_DIR=/srv/cura

# Setup the repositories
RUN mkdir $CURA_BENV_GIT_DIR
WORKDIR $CURA_BENV_GIT_DIR
RUN git clone https://github.com/Ultimaker/Uranium
WORKDIR $CURA_BENV_GIT_DIR/Uranium
RUN git fetch origin
RUN git checkout $URANIUM_BRANCH
RUN git clone https://github.com/Ultimaker/cura
WORKDIR $CURA_BENV_GIT_DIR/Cura
RUN git fetch origin
RUN git checkout origin $CURA_BRANCH

# Ensure Uranium is in the python path
RUN export PYTHOHPATH="${PYTHONPATH}:$CURA_BENV_GIT_DIR/Uranium"

# Run Cura
CMD ["python3", "cura_app.py"]
