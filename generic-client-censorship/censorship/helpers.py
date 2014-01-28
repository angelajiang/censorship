'''List of helper functions for censorship package'''

import socket

def remove_header(url, header):
    '''Return url without header'''
    h_len = len(header)
    if url[:h_len] == header:
        url = url[h_len:]
    return url

def add_header(url, header):
    '''Add header (e.g. http://) to url'''
    h_len = len(header)
    if url[:h_len] != header:
        url= header + url
    return url

def is_ip(s1):
    try:
        socket.inet_aton(s1)
        # legal ip address
        return True
    except socket.error: 
        return False
