# coding=utf-8

from django.core.cache import cache

NODE_ONLINE_KEY = 'node-sync-online:%s'
NODE_SYNC_IN_PROCESS_KEY = 'node-sync-in-progress:%s'
SERVER_IN_DEBUG_MODE_KEY = 'server_in_debug_mode'
SERVER_ALLOW_NODES_KEY = 'server_allow_nodes'
SERVER_STATUS_KEY = 'server_status'


def set_online(node_id, timeout=60):
    cache.set(NODE_ONLINE_KEY % node_id, node_id, timeout)


def get_sync(node_id):
    return cache.get(NODE_SYNC_IN_PROCESS_KEY % node_id)


def set_sync(node_id, timeout=None):
    cache.set(NODE_SYNC_IN_PROCESS_KEY % node_id, True, timeout)


def unset_sync(node_id):
    cache.delete(NODE_SYNC_IN_PROCESS_KEY % node_id)


def server_in_debug_mode():
    return cache.get(SERVER_IN_DEBUG_MODE_KEY)


def server_allow_nodes():
    return cache.get(SERVER_ALLOW_NODES_KEY) or []


def get_status():
    return cache.get(SERVER_STATUS_KEY)


def set_status(value, timeout=None):
    if value:
        cache.set(SERVER_STATUS_KEY, value, timeout)
    else:
        cache.delete(SERVER_STATUS_KEY)


def set_cache(key, value, timeout=60):
    cache.set(key, value, timeout)


def get_cache(key):
    return cache.get(key)


def delete_cache(key):
    cache.delete(key)
