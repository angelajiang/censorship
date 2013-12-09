#! /usr/bin/env python2.7
"""
Censorship test
"""

import socket
import logging
import os
import subprocess
import ConfigParser
import dns.resolver
from time import sleep, time
from threading import Thread
from manager.remote_config import RemoteConfig
import cattle
import traceback

_LOGGER = logging.getLogger(__name__)


class CensorshipTest(Thread):

    def __init__(self):
        _LOGGER.info("Initialized censorship test.")
        Thread.__init__(self)
        self.daemon = True
        self.url = "https://config.aqualab.cs.northwestern.edu/data"
        self.timeout = 21600
        self.cache = 3600
        self.remote_config = RemoteConfig(self)
        self.userApprovement = False
        self.should_run = True

    def getUserApprovement(self):
        """get user's approvement for censorhip test
           This function may be no longer needed"""
        approvement = False

        try:
            config = ConfigParser.RawConfigParser()
            config.read('censorship.cfg')
            approvement = config.getboolean('Censorship', 'approvement')
        except Exception as e:
            _LOGGER.warn("Error on config file %s " % e.__str__())
            p = subprocess.Popen(['python', os.path.dirname(__file__) + '/popup.py'])
            p.wait()
            if p.returncode == 0:
                approvement = True
                _LOGGER.warn("User approved censorship testing")
            else:
                approvement = False
                _LOGGER.warn("User disapproved testing")
            config.add_section('Censorship')
            config.set('Censorship', 'approvement', approvement)
            with open('censorship.cfg', 'w') as configfile:
                config.write(configfile)
        return approvement

    def run(self):
        """Get user's approvement and run the test:
            1. Get url list from the server
            2. Test each of them
            3. Send test results back to the server"""

        #if self.getUserApprovement() == False:
        #    _LOGGER.warn("Censorship test will not run because of user's disagreement")
        #    return
        
        self.should_run = True
        _LOGGER.info("Run censorship test")
        try:
            #get list of urls to test
            response = self.remote_config.get(("namehelp", "experiments", "censorship", "urls"))
            _LOGGER.info("Got response: %s" % str(response))
            urlsToTest = response.get("response", [])
            
            for url in urlsToTest:

                if self.should_run == False:
                    _LOGGER.info("Testing is closed")
                    break
                
                _LOGGER.info("Start testing for: %s" % url)
                timeResponse = time()
                dnsCanResolve, anaLookup, defaultDnsResponse, googleDnsResponse = self.getDNS(url)
                if dnsCanResolve:
                    httpResponse = self.getHTTP(url)
                else:
                    httpResponse = " "

                result = dict()
                result["timeResponse"] = timeResponse
                result["url"] = url
                result["dnsCanResolve"] = dnsCanResolve
                result["anaLookup"] = anaLookup
                result["defaultDnsResponse"] = defaultDnsResponse
                result["googleDnsResponse"] = googleDnsResponse
                result["httpResponse"] = httpResponse


                cattle.report("/test-dns-http", result, project="censorship")
                _LOGGER.info("Finish testing: %s" % url)
                #_LOGGER.info("result: %s" % repr(result))
        
        except Exception, e:
            _LOGGER.error("exception in %s: %s %s\n%s" % (__name__, str(type(e)), str(e), traceback.format_exc()))

    def shutdown(self):
        self.should_run = False
        _LOGGER.info("Censorship test shutting down")

    def getDNS(self, url):
        """do DNS lookup for the url, and return:
           1. If the default DNS server can resolve the URL
           2. Ana lookup for the default DNS server
           3. response of the default DNS server for the URL
           4. response of Google DNS server for the URL"""
        _LOGGER.info("getting DNS")
        dnsCanResolve = True
        defaultDnsResponse = ""
        googleDnsResponse = ""
        anaLookup = ""
        default_dns = dns.resolver.get_default_resolver()
        default_dns.lifetime = 1
        
        try:
            a1 = default_dns.query(url)
            defaultDnsResponse = a1.response.to_text()
        except Exception as e:
            dnsCanResolve = False
            defaultDnsResponse = e.__str__()
            _LOGGER.warn("Failed to get default DNS response")
        try:
            a3 = default_dns.query("nh-%s.ana-aqualab.cs.northwestern.edu" % cattle.getclientid())
            anaLookup = a3.response.to_text()
        except Exception as e:
            anaLookup = e.__str__()
            _LOGGER.warn("Failed to get Ana lookup")
        try:
            default_dns.nameservers = ['8.8.8.8', '8.8.4.4']
            a2 = default_dns.query(url)
            googleDnsResponse = a2.response.to_text()
        except Exception as e:
            googleDnsResponse = e.__str__()
            _LOGGER.warn("Failed to get Google DNS response")

        dns.resolver.restore_system_resolver()
        return (dnsCanResolve, anaLookup, defaultDnsResponse, googleDnsResponse)

    def getHTTP(self, url):
        "get HTTP response with socket and hopefully can detect TCP RST"
        _LOGGER.info("getting HTTP")
        request = "GET / HTTP/1.1\r\nHost: " + url + "\r\n\r\n"
        httpResponse = ""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((url, 80))
            sock.sendall(request)
            while True:
                data = sock.recv(1024)
                httpResponse = httpResponse + data
            sock.close()
            #httpResponse = httpResponse.decode("ISO-8859-1")
        except socket.timeout:
            sock.close()
        except Exception as e:
            httpResponse = e.__str__()
            _LOGGER.warn("Failed to get HTTP response")
        return httpResponse

