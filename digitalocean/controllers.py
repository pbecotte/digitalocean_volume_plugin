from flask import Blueprint, current_app as c, jsonify, request

from .do_api import api_create_volume, api_delete, api_get_volume, api_list_volumes, \
    system_mount_volume, system_unmount_volume
from .exceptions import APIException


routes = Blueprint('routes')

@routes.route('/Plugin.Activate', methods=['POST'])
def handshake():
    return jsonify(Implements=['VolumeDriver'])


@routes.route('/VolumeDriver.Create', methods=['POST'])
def create():
    data = request.get_json(force=True)
    try:
        name = data['Name'].replace('_', '--')
        size = data['Opts']['size']
        api_create_volume(
            name=name,
            size_gigabytes=size,
            description=data['Opts'].get('desc', '')
        )

        return jsonify(Err='')
    except APIException as e:
        return jsonify(Err=str(e))
    except KeyError as e:
        return jsonify(Err='Missing required parameter: %s' % e)


@routes.route('/VolumeDriver.Remove', methods=['POST'])
def remove():
    data = request.get_json(force=True)
    name = data['Name'].replace('_', '--')
    try:
        api_delete(name)
        return jsonify(Err='')
    except APIException as e:
        return jsonify(Err='Failed to remove %s, %s' % (name, e))


@routes.route('/VolumeDriver.Mount', methods=['POST'])
def mount():
    data = request.get_json(force=True)
    name = data['Name'].replace('_', '--')
    id = data['ID']
    try:
        system_mount_volume(name, id)
        return jsonify(Mountpoint='/do_volumes/%s' % name, Err='')
    except APIException as e:
        return jsonify(Err=str(e))


@routes.route('/VolumeDriver.Path', methods=['POST'])
def volume_path():
    data = request.get_json(force=True)
    name = data['Name'].replace('_', '--')
    if c.config['VOLUME_MOUNTS'].get(name):
        return jsonify(Mountpoint='/do_volumes/%s' % name, Err='')
    return jsonify(Err='')


@routes.route('/VolumeDriver.Unmount', methods=['POST'])
def unmount():
    data = request.get_json(force=True)
    name = data['Name'].replace('_', '--')
    id = data['ID']
    try:
        system_unmount_volume(name, id)
        return jsonify(Err='')
    except APIException as e:
        return jsonify(Err=str(e))


@routes.route('/VolumeDriver.Get', methods=['POST'])
def get_volume():
    data = request.get_json(force=True)
    name = data['Name'].replace('_', '--')
    try:
        volume = api_get_volume(name)
        return jsonify(Volume={'Name': volume['name'].replace('--', '_')}, Err='')
    except (APIException, KeyError):
        return jsonify(Err='%s does not exist' % name)


@routes.route('/VolumeDriver.List', methods=['POST'])
def list_volumes():
    err = ''
    volumes = []
    try:
        volumes = [{'name': vol['name'].replace('--', '_')} for vol in api_list_volumes()]
    except APIException as e:
        err = str(e)
    return jsonify(Volumes=volumes, Err=err)


@routes.route('/VolumeDriver.Capabilities', methods=['POST'])
def capabilities():
    return jsonify(Capabilities={
        "Scope": "global"
    })
