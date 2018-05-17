import struct

class Transfer:

    def __init__(self, socket):
        self.sock = socket

    def send(self, msg):
        # Prefix each message with a 4-byte length (network byte order)
        try:
            msg = struct.pack('>I', len(msg)) + msg
            self.sock.sendall(msg)
        except:
            raise

    def recv(self):
        # Read message length and unpack it into an integer
        try:
            raw_msglen = self.recvall(4)
            if not raw_msglen:
                return None
            msglen = struct.unpack('>I', raw_msglen)[0]
        except:
            raise

        # Read the message data
        return self.recvall(msglen)

    def recvall(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        try:
            data = b''
            while len(data) < n:
                packet = self.sock.recv(n - len(data))
                if not packet:
                    return None
                data += packet
        except:
            raise
        return data