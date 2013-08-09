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
        sender = self.addHost('sender', ip='10.0.1.1', mac='00:00:00:00:00:01')
        LTE = self.addHost('LTE', ip='0.0.0.0')
        receiver = self.addHost('receiver', ip='10.0.1.2', mac='00:00:00:00:00:02')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # Add links
        self.addLink(sender, s1)
        self.addLink(s1, LTE)
        self.addLink(LTE, s2)
        self.addLink(s2, receiver)

def set_all_IP(net, sender, LTE, receiver):
    sender.sendCmd('ifconfig sender-eth0 10.0.1.1 netmask 255.255.255.0')
    sender.waitOutput()
    LTE.sendCmd('ifconfig LTE-eth0 up')
    LTE.waitOutput()
    LTE.sendCmd('ifconfig LTE-eth1 up')
    LTE.waitOutput()
    receiver.sendCmd('ifconfig receiver-eth0 10.0.1.2 netmask 255.255.255.0')
    receiver.waitOutput()

    sender.sendCmd('echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6')
    sender.waitOutput()
    LTE.sendCmd('echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6')
    LTE.waitOutput()
    receiver.sendCmd('echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6')
    receiver.waitOutput()

def display_routes(net, sender, LTE, receiver):
    print 'sender route...'
    sender.sendCmd('route -n')
    print sender.waitOutput()
    print 'LTE route...'
    LTE.sendCmd('route -n')
    print LTE.waitOutput()
    print 'receiver route...'
    receiver.sendCmd('route -n')
    print receiver.waitOutput()

def run_cellsim(LTE):
    LTE.sendCmd('/home/ubuntu/multisend/sender/cellsim-setup.sh LTE-eth0 LTE-eth1')
    LTE.waitOutput()
    print "Running cellsim (this will take a few minutes)..."
    LTE.sendCmd('/home/ubuntu/cell-codel/cellsim-runner.sh')
    LTE.waitOutput()
    print "done."

def run_apache(sender):
    print "Starting apache server..."
    sender.cmdPrint('/usr/sbin/apache2ctl -f /etc/apache2/apache2.conf')
    sender.waitOutput()
    print "done."

def run_flowrequestr(receiver):
    print "Starting Flow Requestr at the receiver...",
    receiver.sendCmd('/home/ubuntu/cell-codel/workloads/on-off.py 10.0.1.1 150 persistent 1 > /tmp/flowreq.stdout 2> /tmp/flowreq.stderr &')
    receiver.waitOutput()
    print "done"

def print_welcome_message():
    print "####################################################################"
    print "#                                                                  #"
    print "#               6.829 PS 2 Emulated Network Test                   #"
    print "#                                                                  #"
    print "#          running sender <=> cellsim <=> receiver                 #"
    print "#                                                                  #"
    print "#  Debug output in /tmp/{sender,receiver,cellsim}-{stdout,stderr}  #"
    print "#                                                                  #"
    print "####################################################################"
    print

def run_cellsim_topology():
    print_welcome_message()

    os.system( "killall -q controller" )
    os.system( "killall -q cellsim" )
    os.system( "killall -q datagrump-sender" )
    os.system( "killall -q datagrump-receiver" )
    os.system( "service apache2 stop" )
    os.system( "killall -q apache2" )
    os.system( "killall -q on-off.py")

    topo = ProtoTester()
    net = Mininet(topo=topo, host=Host, link=Link)
    net.start()

    sender = net.getNodeByName('sender')
    LTE = net.getNodeByName('LTE')
    receiver = net.getNodeByName('receiver')

    set_all_IP(net, sender, LTE, receiver)
    
    #Dump connections
    #dumpNodeConnections(net.hosts)
    #display_routes(net, sender, LTE, receiver)

    run_apache(sender)
    run_flowrequestr(receiver)

    run_cellsim(LTE)

#    CLI(net)

    net.stop()

def upload_data( username ):
    print "Uploading data to server...",
    os.system('grep "%" /tmp/cellsim-stderr | grep downlink > /tmp/utils')
    os.system( 'gnuplot -p plot.p')
    os.system( 'scp downlink.png anirudh@anirudh.csail.mit.edu:~' );
    print "done"

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: sudo %s [username]" % sys.argv[ 0 ]
    else:
        run_cellsim_topology()
        upload_data( sys.argv[ 1 ] )
