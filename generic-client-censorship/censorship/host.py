"""
Modules for tests of censorship

Author: Angela Jiang <angelajiang2014@u.northwestern.edu>
"""

# Only use integers separated by periods. 
# Don't use letters to indicate maturity
#   (e.g. a or b for alpha or beta).
__version__ = "1.0"

import socket
import urllib

class Host():

    def __init__(self):
        self.origin = urllib.urlopen('http://www.biranchi.com/ip.php').read()
        return

    def dnsRedirect(self):
        print self.origin
        try:
            dest = socket.gethostbyname('angela.google.com')
        except:
            print 'hostname not found\n'
        return




