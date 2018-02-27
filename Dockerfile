FROM ultimaker/cura-build-environment:3.2

# Environment vars for easy configuration
ENV CURA_BRANCH=master
ENV URANIUM_BRANCH=$CURA_BRANCH
ENV CURA_BENV_GIT_DIR=/srv/cura

RUN mkdir $CURA_BENV_GIT_DIR

# Setup Uranium
WORKDIR $CURA_BENV_GIT_DIR
RUN git clone https://github.com/Ultimaker/Uranium
WORKDIR $CURA_BENV_GIT_DIR/Uranium
RUN git fetch origin
RUN git checkout $URANIUM_BRANCH
RUN export PYTHOHPATH="${PYTHONPATH}:$CURA_BENV_GIT_DIR/Uranium"

# Setup Cura
WORKDIR $CURA_BENV_GIT_DIR
RUN git clone https://github.com/Ultimaker/cura
WORKDIR $CURA_BENV_GIT_DIR/Cura
RUN git fetch origin
RUN git checkout origin $CURA_BRANCH

# Run Cura
WORKDIR $CURA_BENV_GIT_DIR/Cura
CMD ["python3", "cura_app.py"]
