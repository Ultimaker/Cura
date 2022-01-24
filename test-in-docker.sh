sudo rm -rf ./build ./Uranium
sudo docker run -it --rm \
  -v "$(pwd):/srv/cura" ultimaker/cura-build-environment \
  /srv/cura/docker/build.sh
sudo rm -rf ./build ./Uranium
