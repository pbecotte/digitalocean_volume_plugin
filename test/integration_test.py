import machine
import docker
m = machine.Machine(path="/usr/local/bin/docker-machine")
client = docker.Client(**m.config(machine='default'))
client.ping()
