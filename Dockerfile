FROM ultimaker/cura-build-environment:3.2

# Environment vars for easy configuration
ENV CURA_BENV_BUILD_TYPE=Release
ENV CURA_BRANCH=master
ENV URANIUM_BRANCH=$CURA_BRANCH
ENV CURA_ENGINE_BRANCH=$CURA_BRANCH
ENV CURA_APP_DIR=/srv/cura

RUN mkdir $CURA_APP_DIR

# Setup Uranium
WORKDIR $CURA_APP_DIR
RUN git clone https://github.com/Ultimaker/Uranium
WORKDIR $CURA_APP_DIR/Uranium
RUN git fetch origin
RUN git checkout $URANIUM_BRANCH
RUN export PYTHOHPATH="${PYTHONPATH}:$CURA_APP_DIR/Uranium"

# Setup Cura
WORKDIR $CURA_APP_DIR
RUN git clone https://github.com/Ultimaker/Cura
WORKDIR $CURA_APP_DIR/Cura
RUN git fetch origin
RUN git checkout origin $CURA_BRANCH

# Setup CuraEngine
WORKDIR $CURA_APP_DIR
RUN git clone https://github.com/Ultimaker/CuraEngine
WORKDIR $CURA_APP_DIR/CuraEngine
RUN git fetch origin
RUN git checkout $URANIUM_BRANCH
RUN mkdir build
WORKDIR $CURA_APP_DIR/CuraEngine/build
RUN cmake3 .. \
    -DCMAKE_BUILD_TYPE=$CURA_BENV_BUILD_TYPE \
    -DCMAKE_C_COMPILER=gcc \
    -DCMAKE_CXX_COMPILER=g++
RUN make

# Make sure Cura can find CuraEngine
RUN ln -s /usr/local/bin/CuraEngine $CURA_APP_DIR/Cura

# Run Cura
WORKDIR $CURA_APP_DIR/Cura
CMD ["python3", "cura_app.py"]
