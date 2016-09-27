import subprocess
from time import sleep

from flask import current_app as c
import requests

from .exceptions import APIException


def api_get_metadata():
    response = requests.get('http://169.254.169.254/metadata/v1/id')
    if not response.status_code == 200:
        raise APIException()
    id = response.text
    response = requests.get('http://169.254.169.254/metadata/v1/region')
    if not response.status_code == 200:
        raise APIException()
    region = response.text
    return id, region

def send_request(endpoint, method, data=None, params=None):
    base = 'https://api.digitalocean.com'
    headers = {'Authorization': 'Bearer %s' % c.config['TOKEN'], 'Content-Type': 'application/json'}
    return method(base + endpoint, headers=headers, json=data, params=params)


def api_get_volume(name):
    params = {'name': name, 'region': c.config['REGION']}
    response = send_request('/v2/volumes', requests.get, params=params)
    if not response.status_code == 200:
        raise APIException()
    volumes = response.json()['volumes']
    return volumes[0] if len(volumes) else {}


def api_list_volumes():
    response = send_request('/v2/volumes', requests.get)
    if not response.status_code == 200:
        raise APIException()
    return response.json()['volumes']


def api_create_volume(name, size_gigabytes, description):
    data = {
        'name': name,
        'size_gigabytes': size_gigabytes,
        'description': description,
        'region': c.config['REGION']
    }

    response = send_request('/v2/volumes', requests.post, data=data)
    if not response.status_code == 201:
        raise APIException(response.json()['message'])

    api_mount_volume(name)
    dev = '/dev/disk/by-id/scsi-0DO_Volume_%s' % name
    sleep(1)
    subprocess.check_output('parted %s mklabel -s gpt' % dev, shell=True)
    subprocess.check_output('parted -a opt %s mkpart primary ext4 0%% 100%%' % dev, shell=True)
    sleep(1)
    subprocess.check_output('mkfs.ext4 -F %s-part1' % dev, shell=True)
    api_unmount_volume(name)


def api_mount_volume(name):
    data = {
        'type': 'attach',
        'droplet_id': c.config['DROPLET_ID'],
        'volume_name': name,
        'region': c.config['REGION']
    }
    response = send_request('/v2/volumes/actions', requests.post, data=data)
    if not response.status_code == 202:
        raise APIException(response.json()['message'])
    action = response.json()['action']
    status = action['status']
    while status == 'in-progress':
        response = send_request('/v2/actions/%s' % action['id'], method=requests.get)
        if not response.status_code == 200:
            raise APIException(response.json()['message'])
        action = response.json()['action']
        status = action['status']
    if status == 'errored':
        raise APIException('Failed to attach Volume')


def api_unmount_volume(name, droplet_id=None):
    if droplet_id is None:
        droplet_id = c.config['DROPLET_ID']
    data = {
        'type': 'detach',
        'droplet_id': droplet_id,
        'volume_name': name,
        'region': c.config['REGION']
    }
    response = send_request('/v2/volumes/actions', requests.post, data=data)
    if not response.status_code == 202:
        raise APIException(response.json()['message'])
    action = response.json()['action']
    status = action['status']
    while status == 'in-progress':
        response = send_request('/v2/actions/%s' % action['id'], method=requests.get)
        if not response.status_code == 200:
            raise APIException(response.json()['message'])
        action = response.json()['action']
        status = action['status']
    if status == 'errored':
        raise APIException('Failed to detach Volume')


def api_delete(name):
    params = {'name': name, 'region': c.config['REGION']}
    vol = api_get_volume(name)
    if len(vol.get('droplet_ids', [])):
        raise APIException('Volume is already attached')
    response = send_request('/v2/volumes', requests.delete, params=params)
    if not response.status_code == 204:
        raise APIException(response.json()['message'])



def system_mount_volume(name, id):
    if c.config['VOLUME_MOUNTS'].get(name):
        c.config['VOLUME_MOUNTS'][name].append(id)
        return
    vol = api_get_volume(name)
    if len(vol.get('droplet_ids', [])):
        if str(vol.get('droplet_ids')[0]) == str(c.config['DROPLET_ID']):
            perform_mount(name)
            return
        raise APIException('Volume is already attached to another Droplet')
    try:
        api_mount_volume(name)
        perform_mount(name)
    except subprocess.CalledProcessError as e:
        raise APIException(str(e))


def perform_mount(name):
    dev = '/dev/disk/by-id/scsi-0DO_Volume_%s' % name
    subprocess.check_output('mkdir -p /do_volumes/%s' % name, shell=True)
    try:
        subprocess.check_output('mountpoint /do_volumes/%s' % name, shell=True)
    except subprocess.CalledProcessError:
        subprocess.check_output('mount -t ext4 -o rw,rshared %s-part1  /do_volumes/%s' % (dev, name),
                            shell=True)
    c.config['VOLUME_MOUNTS'][name] = [id]


def system_unmount_volume(name, id):
    if c.config['VOLUME_MOUNTS'].get(name):
        c.config['VOLUME_MOUNTS'].get(name).remove(id)
    if not c.config['VOLUME_MOUNTS'].get(name):
        try:
            subprocess.check_output('umount -d /dev/disk/by-id/scsi-0DO_Volume_%s-part1' % name, shell=True)
        except subprocess.CalledProcessError as e:
            raise APIException(str(e))
        api_unmount_volume(name)
