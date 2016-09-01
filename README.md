This is a Docker plugin that allows you to connect Digital Ocean Block
Store Volumes to your Droplets and mount them for Docker Volumes.

# Disclaimer

This app is Alpha or Beta quality- it is my first time writing a Docker
plugin or even really dealing with device mounting extensively.  I
promise you will find bugs!

# Install

The plugin runs easily as a Docker Container-

```sh
docker run \
    -v /dev:/dev \
    -v /run/docker/plugins:/run/docker/plugins \
    -v /do_volumes/:/do_volumes:rshared \
    --privileged \
    -e DIGITAL_OCEAN_TOKEN=<MY DO API TOKEN> \
    pbecotte/digital_ocean_volumes
```

It requires privileged and /dev to actually mount the device once
connected, plus your Digital Ocean api key as an env variable.  It is
important to note, if your Docker Daemon is being run under Systemd, you
must ensure that `MountFlags=slave` is not set in your unit file- it
break the `rshared` setting and prevent this from running.  If you
installed with Docker Machine, you probably have such a file at 
`/etc/systemd/system/docker.service`.

# Commands

`docker volume ls` will include a list of all the DO volumes in your
account for the region the droplet is in.

`docker volume create -d digitalocean -o size=5 -o desc='some 
description' --name myvolume` would create a DO volume with the given 
name, size, and description in the same region as the droplet.  Size 
and Name are required.  This does NOT attach the volume to the droplet.

`docker volume rm myvolume` if myvolume is a DO volume, this will
permanently delete your Volume.

`docker run -v myvolume:/app ubuntu ls /app` This would mount the block
volume, attach it to the new container, and then print out the contents.
When the container exits, the volume will be detached from the droplet.
If more than one container on a single droplet attach to the same
volume, it will stay attached until the last one exits.  If the volume
is already attached to another droplet, this command will fail.
