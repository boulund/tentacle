from __future__ import print_function

import zerorpc
import gevent
import zmq
import random
import socket
import itertools
from math import floor

from utils.scope import Scope

def bind_to_free_port(server, addr, min_port=49152, max_port=65536, max_tries=100):
    """Mimicking zmq.Socket.bind_to_free_port(...), which is hidden by wrapper classes. 
    See http://zeromq.github.com/pyzmq/api/zmq.html"""
    #Try a few non-random ports first, to get the same ports when repeatedly debugging.
    nd = int(floor(max_tries/10))
    candidate_ports = itertools.chain( xrange(min_port, min_port+nd), random.sample(xrange(min_port+nd,max_port+1),max_tries-nd) )
    for port in candidate_ports:
        try:
            print("Attempting to bind to: " + addr + ":" + str(port))
            server.bind(addr + ":" + str(port))
            return port
        except zmq.core.error.ZMQError as e:
            if e.errno == 48: #Address already in use, try another port
                pass #Do nothing
            else:
                raise e
    raise zmq.core.error.ZMQBindError("Could not bind socket to random port.")
        
def get_ip_addresses():
    return [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]

def create_server(functor):
    s = zerorpc.Server(functor)
    addr = "tcp://0.0.0.0"
    port = bind_to_free_port(s, addr)
    addresses = ["tcp://{}:{}".format(ip,port) for ip in get_ip_addresses()]
    return s, addresses

def run_single_rpc(remote_endpoint, functor):
    with Scope() as scope:
        client = zerorpc.Client()
        scope.on_exit(client.close)
        client.connect(remote_endpoint)
        return functor(client)
