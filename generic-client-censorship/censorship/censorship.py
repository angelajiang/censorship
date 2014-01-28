#! /usr/bin/env python2.7
"""
Censorship test
"""

import socket
import logging
import os
import subprocess
import urllib2
import ConfigParser
import dns.resolver
from pprint import pprint
from time import sleep, time
from threading import Thread
from manager.remote_config import RemoteConfig

import cattle
import traceback
import geturls
import helpers

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
        #Get user's approvement for censorship test
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
            """ Get list of URLs to test"""
            response = self.remote_config.get(("namehelp", "experiments", "censorship", "urls"))
            _LOGGER.info("Got response: %s" % str(response))
            urlsToTest = response.get("response", [])
            # Currently gets static list of globally censored urls
            urlsToTest = geturls.get_urls_by_area('/Users/angelajiang/code/repos/censorship/generic-client-censorship/censorship/urls.db', 'urllist', 'glo')
            
            for url in urlsToTest:
                if self.should_run == False:
                    _LOGGER.info("Testing is closed")
                    break
                if helpers.is_ip(url):
                    _LOGGER.info('URL is an IP address\n\n\n\n\n')
                    continue
                _LOGGER.info("Start testing for: %s" % url)
                timeResponse = time()
                dnsResults = self.getDNS(url)
                if dnsResults['dnsCanResolve']:
                    httpResults = self.getHTTP(url)
                else:
                    httpResults= None

                result = dict()
                result["timeResponse"] = timeResponse
                result["url"] = url
                result['dnsResults'] = dnsResults
                result["httpResults"] = httpResults
                pprint(httpResults) 
                #reporting /test-dns or test-collateral
                cattle.report("/test-dns-http", result, project="censorship")
                _LOGGER.info("Finish testing: %s\n" % url)
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
        dnsRedirected = True
        anaLookup = ""
        default_dns = dns.resolver.get_default_resolver()
        default_dns.lifetime = 1
        fakeurl = url.split('.') 
        fakeurl.append('fake')
        fakeurl = ('.').join(fakeurl)

        #Use default DNS
        try:
            a1 = default_dns.query(url)
            defaultDnsResponse = a1.response.to_text()
            _LOGGER.warn("default dns: SUCCESS")
        except Exception as e:
            dnsCanResolve = False
            defaultDnsResponse = e.__str__()
            _LOGGER.warn("default dns: FAIL")
            _LOGGER.warn(defaultDnsResponse)

        google_dns = dns.resolver.get_default_resolver()
        google_dns.lifetime = 1

        #Use default DNS to test for DNS injection/redirection
        try:
            b1 = default_dns.query(fakeurl)
            redirectDnsResponse = b1.response.to_text()
            _LOGGER.warn("dns injection: DETECTED")
        except Exception as e:
            dnsRedirected = False
            redirectDnsResponse = e.__str__()
            warning = "dns injection: NOT DETECTED "
            _LOGGER.warn(warning)

        #ANA lookup
        try:
            a3 = default_dns.query("nh-%s.ana-aqualab.cs.northwestern.edu" % cattle.getclientid())
            anaLookup = a3.response.to_text()
            _LOGGER.warn("ana lookup: SUCCESS")
        except Exception as e:
            anaLookup = e.__str__()
            _LOGGER.warn("ana lookup: FAIL")
        try:
            google_dns.nameservers = ['8.8.8.8', '8.8.4.4']
            a2 = google_dns.query(url)
            googleDnsResponse = a2.response.to_text()
            _LOGGER.warn("google dns: SUCCESS")
        except Exception as e:
            googleDnsResponse = e.__str__()
            _LOGGER.warn("google dns: FAIL")

        dns.resolver.restore_system_resolver()

        dnsResults = dict(dnsCanResolve=dnsCanResolve, anaLookup=anaLookup,defaultDnsResponse=defaultDnsResponse,dnsRedirected=dnsRedirected, redirectDnsResponse=redirectDnsResponse, googleDnsResponse=googleDnsResponse)
        return dnsResults

    def getHTTP(self, url):
        '''Try to get content. If no response, try to set up TCP connection'''
        http_results = dict(canGetContent=False, content='')
        _LOGGER.info("Starting HTTP tests")
        url_with_http = helpers.add_header(url, "http://")
        try:
            content = urllib2.urlopen(url_with_http).read()
            _LOGGER.warn("get content from url: SUCCESS")
            http_results['canGetContent'] = True
            http_results['content'] = content
        except:
            _LOGGER.warn("get content from url: FAIL")
            
        request = "GET / HTTP/1.1\r\nHost: " + url + "\r\n\r\n"
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
        return http_results

