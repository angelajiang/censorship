'''List of helper functions for censorship package'''

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

