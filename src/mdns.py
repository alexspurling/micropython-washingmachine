"""Discover Home Assistant on the local network via mDNS/DNS-SD.

Queries the multicast DNS service type _home-assistant._tcp.local
and returns the first matching IP:port pair.

MicroPython implementation — no dependencies beyond socket and struct.
"""
import struct
import socket
import time

# mDNS well-known multicast address and port
MDNS_ADDR = '224.0.0.251'
MDNS_PORT = 5353

# Service type that Home Assistant advertises
HA_SERVICE = '_home-assistant._tcp.local'


def _build_mdns_query():
    """Build a DNS-SD query packet for _home-assistant._tcp.local."""
    # Encode the query name with DNS label compression:
    # each label is length-prefixed, terminated by a zero-length label.
    parts = HA_SERVICE.split('.')
    name = b''
    for part in parts:
        if part:
            name += bytes([len(part)]) + part.encode()
    name += b'\x00'  # terminating zero-length label

    # DNS header: Transaction ID=0, flags=0x0100 (standard query), QDCOUNT=1
    tid = 0x0000
    flags = 0x0100  # recursion desired
    qdcount = 1
    ancount = nscount = arcount = 0

    header = struct.pack('>HHHHHH', tid, flags, qdcount, ancount, nscount, arcount)

    # Question section: PTR query (QTYPE=12, QCLASS=0x8001 = IN + unicast-response bit)
    qtype = 12       # PTR
    qclass = 0x8001  # IN + unicast-response

    question = name + struct.pack('>HH', qtype, qclass)

    return header + question


def _parse_mdns_response(data):
    """Extract hostname and IP:port from an mDNS response.

    Returns (hostname, ip, port) or None.
    Only handles a single answer chain (PTR -> SRV -> A).
    """
    try:
        # Skip the DNS header (12 bytes)
        offset = 12

        # Skip question section — we have to read past it
        # Each label in the name is length-prefixed; terminated by \x00
        while offset < len(data):
            length = data[offset]
            if length == 0:
                offset += 1
                break
            offset += length + 1
        else:
            return None

        # Skip qtype and qclass (4 bytes)
        offset += 4

        # Parse answer records
        ptr_target = None
        srv_target = None
        srv_port = None
        a_record_ip = None

        while offset + 12 <= len(data):
            # Name (could be compressed with pointer 0xC0XX)
            if data[offset] & 0xC0 == 0xC0:
                offset += 2
            else:
                while offset < len(data):
                    length = data[offset]
                    if length == 0:
                        offset += 1
                        break
                    offset += length + 1
                else:
                    break

            if offset + 10 > len(data):
                break

            rtype, rclass, ttl, rdlength = struct.unpack('>HHiH', data[offset:offset + 10])
            offset += 10

            if offset + rdlength > len(data):
                break

            rdata = data[offset:offset + rdlength]

            if rtype == 12:  # PTR
                target = _decode_name(rdata, 0, data)
                if target:
                    ptr_target = target
            elif rtype == 33:  # SRV
                # RDATA: priority (2), weight (2), port (2), target (variable)
                if rdlength >= 6:
                    srv_port = struct.unpack('>H', rdata[4:6])[0]
                    target = _decode_name(rdata, 6, data)
                    if target:
                        srv_target = target
            elif rtype == 1:  # A
                if rdlength == 4:
                    a_record_ip = '{}.{}.{}.{}'.format(*rdata)

            offset += rdlength

        if a_record_ip and srv_port:
            hostname = srv_target or ptr_target or 'home-assistant.local'
            return (hostname, a_record_ip, srv_port)

        return None

    except IndexError:  # malformed or truncated mDNS response
        return None


def _decode_name(packet, offset, full_packet):
    """Decode a DNS name from a packet at the given offset."""
    labels = []
    while offset < len(packet):
        length = packet[offset]
        if length == 0:
            offset += 1
            break
        if length & 0xC0 == 0xC0:  # Name compression pointer (14-bit offset)
            ptr = ((length & 0x3F) << 8) | packet[offset + 1]
            more = _decode_name(full_packet, ptr, full_packet)
            if more:
                labels.append(more)
            offset += 2
            break
        offset += 1
        if offset + length > len(packet):
            return None
        labels.append(packet[offset:offset + length].decode())
        offset += length
    else:
        return None
    return '.'.join(labels)


def discover(timeout_sec=2):
    """Send an mDNS query for Home Assistant and return (hostname, ip, port).

    Returns None if nothing responds within *timeout_sec* seconds.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(timeout_sec)

        query = _build_mdns_query()

        # Send the query to the mDNS multicast address
        s.sendto(query, (MDNS_ADDR, MDNS_PORT))

        deadline = time.time() + timeout_sec

        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            s.settimeout(remaining)
            try:
                data, addr = s.recvfrom(1024)
            except OSError:
                # Timeout or no data
                break

            result = _parse_mdns_response(data)
            if result:
                s.close()
                return result

        s.close()
        return None

    except OSError as e:
        print('mDNS error:', e)
        return None