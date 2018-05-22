import os, socket, nfqueue
from scapy.all import *
from entities.job import *
from thread import Thread
from modules.utility import printLog

class feeRemovalThread(Thread):

    """
        Class for creating thread to alter the network package when miner dev fee is processed
        This class utilizes python nfqueue to alter the network package payload.

        Package Network Address
            Miner must define the developer pool ports and listening ports that will be used
            by iptables when redirecting network packages to nfqueue

        Package Alteration
            Corresponding miner instance must have processFeePayload method that performs the package
            payload alteration.

    """

    def __init__(self, start, Miner):
        self.active = False
        self.job = False
        self.miner = Miner
        self.wallet = self.miner.wallet
        self.address = self.miner.raw_url
        self.port = self.miner.port
        self.listening_ports = self.miner.listening_ports
        self.pool_ip_address = socket.gethostbyname(self.address)
        self.dev_pool_ports = self.miner.dev_pool_ports
        self.dev_ip_addresses = []

        if self.port not in self.listening_ports:
            self.listening_ports.append(self.port)

        self.init()
        if start:
            self.start()




    def init(self):
        command = "iptables -A OUTPUT -p tcp --match multiport --dports %s -j NFQUEUE --queue-num 0" % (','.join(str(v) for v in self.listening_ports))
        os.system(command)

        command = "iptables -t nat -A OUTPUT -p tcp --match multiport --dports %s -j DNAT --to-destination %s:%s" % (','.join(str(v) for v in self.dev_pool_ports), self.pool_ip_address, self.port)
        os.system(command)

        if self.dev_ip_addresses:
            command = "iptables -t nat -A OUTPUT -p tcp -d %s -j DNAT --to-destination %s:%s" % (','.join(str(v) for v in self.dev_ip_addresses), self.pool_ip_address, self.port)
            os.system(command)

        self.job = Job(1, self.update)
        self.queue = nfqueue.queue()
        self.queue.open()
        self.queue.bind(socket.AF_INET)
        self.queue.set_callback(self.process)
        self.queue.create_queue(0)



    def update(self, runner):
        self.queue.process_pending(1)



    def process(self, arg1, payload):
        data = payload.get_data()
        pkt = IP(data)

        payload_before = len(pkt[TCP].payload)
        payload_text = str(pkt[TCP].payload)
        new_payload_text = self.miner.processFeePayload(self, arg1, payload, payload_text, pkt)

        if new_payload_text:
            printLog('Replaced DevFee for %s miner' % (self.miner.miner), 'success')
            payload_text = new_payload_text
            if pkt[IP].dst != self.pool_ip_address:
                if pkt[IP].dst not in self.dev_ip_addresses:
                    self.dev_ip_addresses.append(pkt[IP].dst)
                    command = "iptables -t nat -A OUTPUT -p tcp -d %s -j DNAT --to-destination %s:%s" % (pkt[IP].dst, self.pool_ip_address, self.pool_port)
                    os.system(command)

            pkt[IP].dst = self.pool_ip_address
            pkt[TCP].payload = payload_text
            payload_after = len(payload_text)
            payload_dif = payload_after - payload_before
            pkt[IP].len = pkt[IP].len + payload_dif
            pkt[IP].ttl = 40

            del pkt[IP].chksum
            del pkt[TCP].chksum
            payload.set_verdict_modified(nfqueue.NF_ACCEPT, str(pkt), len(pkt))

