#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Host
from mininet.link import Link
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.util import ensureRoot

from subprocess import Popen, PIPE
from time import sleep, time

import sys
import os
import math
import requests

ensureRoot()

class ProtoTester(Topo):
    def __init__(self):
        
        # Initialise topology
        Topo.__init__(self)

        # Add hosts and switches
        server = self.addHost('server', ip='10.0.1.1', mac='00:00:00:00:00:01')
        LTE = self.addHost('LTE', ip='0.0.0.0')
        client = self.addHost('client', ip='10.0.1.2', mac='00:00:00:00:00:02')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # Add links
        self.addLink(server, s1)
        self.addLink(s1, LTE)
        self.addLink(LTE, s2)
        self.addLink(s2, client)

def set_all_IP(net, server, LTE, client):
    server.sendCmd('ifconfig server-eth0 10.0.1.1 netmask 255.255.255.0')
    server.waitOutput()
    LTE.sendCmd('ifconfig LTE-eth0 up')
    LTE.waitOutput()
    LTE.sendCmd('ifconfig LTE-eth1 up')
    LTE.waitOutput()
    client.sendCmd('ifconfig client-eth0 10.0.1.2 netmask 255.255.255.0')
    client.waitOutput()

    server.sendCmd('echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6')
    server.waitOutput()
    LTE.sendCmd('echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6')
    LTE.waitOutput()
    client.sendCmd('echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6')
    client.waitOutput()

def display_routes(net, server, LTE, client):
    print 'server route...'
    server.sendCmd('route -n')
    print server.waitOutput()
    print 'LTE route...'
    LTE.sendCmd('route -n')
    print LTE.waitOutput()
    print 'client route...'
    client.sendCmd('route -n')
    print client.waitOutput()

def run_cellsim(LTE):
    LTE.sendCmd('/home/ubuntu/multisend/sender/cellsim-setup.sh LTE-eth0 LTE-eth1')
    LTE.waitOutput()
    print "Running cellsim (this will take a few minutes)..."
    LTE.sendCmd('/home/ubuntu/multisend/sender/cellsim-runner.sh')
    LTE.waitOutput()
    print "done."

def run_web(server, client):
    print "Running web client...",
    client.sendCmd('/home/ubuntu/web-benchmarks/phantomjs/bin/phantomjs  /home/ubuntu/web-benchmarks/phantomjs/examples/loadspeed.js http://10.0.1.1/rand.jpg > /tmp/client-stdout 2> /tmp/client-stderr &')
    client.waitOutput()
    print "done."
    print "Running web server...",
    server.sendCmd('sudo service apache2 stop && sudo service apache2 start')
    server.waitOutput()
    print "done."

def print_welcome_message():
    print "####################################################################"
    print "#                                                                  #"
    print "#               6.829 PS 2 Emulated Network Test                   #"
    print "#                                                                  #"
    print "#          running server <=> cellsim <=> client                 #"
    print "#                                                                  #"
    print "#  Debug output in /tmp/{server,client,cellsim}-{stdout,stderr}  #"
    print "#                                                                  #"
    print "####################################################################"
    print

def run_cellsim_topology():
    print_welcome_message()

    os.system( "killall -q controller" )
    os.system( "killall -q cellsim" )
    os.system( "killall -q phantomjs" )

    topo = ProtoTester()
    net = Mininet(topo=topo, host=Host, link=Link)
    net.start()

    server = net.getNodeByName('server')
    LTE = net.getNodeByName('LTE')
    client = net.getNodeByName('client')

    set_all_IP(net, server, LTE, client)
    
    #Dump connections
    #dumpNodeConnections(net.hosts)
    #display_routes(net, server, LTE, client)

    run_web(server, client)

    run_cellsim(LTE)

#    CLI(net)

    net.stop()

def upload_data( username ):
    print "Uploading data to server...",
    os.system( 'gzip --stdout /tmp/cellsim-stdout > /tmp/to-upload.gz' )
    reply = requests.post( 'http://6829.keithw.org/cgi-bin/6829/upload-data',
                           files={'contents': (username, open( '/tmp/to-upload.gz',
                                                               'rb' ))} )
    print "done. Got reply:"
    print
    print reply.text

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: sudo %s [username]" % sys.argv[ 0 ]
    else:
        run_cellsim_topology()
        upload_data( sys.argv[ 1 ] )
