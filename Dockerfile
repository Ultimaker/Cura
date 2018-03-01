FROM ultimaker/cura-build-environment:1

# Environment vars for easy configuration
ENV CURA_BENV_BUILD_TYPE=Release
ENV CURA_BRANCH=3.2
ENV URANIUM_BRANCH=$CURA_BRANCH
ENV CURA_ENGINE_BRANCH=$CURA_BRANCH
ENV MATERIALS_BRANCH=$CURA_BRANCH
ENV CURA_APP_DIR=/srv/cura

# Ensure our sources dir exists
RUN mkdir $CURA_APP_DIR

# Setup Uranium
WORKDIR $CURA_APP_DIR
RUN git clone -b $URANIUM_BRANCH --depth 1 https://github.com/Ultimaker/Uranium
WORKDIR $CURA_APP_DIR/Uranium

# Setup Cura
WORKDIR $CURA_APP_DIR
RUN git clone -b $CURA_BRANCH --depth 1 https://github.com/Ultimaker/Cura
WORKDIR $CURA_APP_DIR/Cura

# Setup materials
WORKDIR $CURA_APP_DIR/Cura/resources
RUN git clone -b $MATERIALS_BRANCH --depth 1 https://github.com/Ultimaker/fdm_materials materials
WORKDIR $CURA_APP_DIR/Cura/resources/materials

# Setup CuraEngine
WORKDIR $CURA_APP_DIR
RUN git clone -b $CURA_ENGINE_BRANCH --depth 1 https://github.com/Ultimaker/CuraEngine
WORKDIR $CURA_APP_DIR/CuraEngine
RUN mkdir build
WORKDIR $CURA_APP_DIR/CuraEngine/build
RUN cmake3 ..
RUN make
RUN make install

# TODO: setup libCharon

# Make sure Cura can find CuraEngine
RUN ln -s /usr/local/bin/CuraEngine $CURA_APP_DIR/Cura

# Tmp cleanup
RUN rm -Rf /var/cache

# Run Cura
WORKDIR $CURA_APP_DIR/Cura
ENV PYTHONPATH=${PYTHONPATH}:$CURA_APP_DIR/Uranium
ENV DISPLAY=:1.0
ADD run_in_docker.sh .
RUN chmod +x ./run_in_docker.sh
CMD "./run_in_docker.sh"
