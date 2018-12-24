import struct

class Transfer:

    """
        Class for handling socket transfers
        The package packet expected to have 4 bytes struct at the beginning
    """

    def __init__(self, socket):
        self.sock = socket

    def send(self, msg):
        # Prefix each message with a 4-byte length (network byte order)
        msg = struct.pack('>I', len(msg)) + msg
        self.sock.sendall(msg)


    def recv(self):
        # Read message length and unpack it into an integer
        raw_msglen = self.recvall(4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]

        # Read the message data
        return self.recvall(msglen)


    def recvall(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = b''
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                if len(data) > 0:
                    return data
                else:
                    return None

            data += packet
        return data