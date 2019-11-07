# -*- coding: utf-8 -*-

import sys

if sys.version_info[:2] > (2,7):
    import http.server as SimpleHTTPServer
    import socketserver as SocketServer
    from urllib.parse import urlparse, parse_qs, parse_qsl

if sys.version_info[:2] <= (2,7):
    import SimpleHTTPServer 
    import SocketServer 
    from urlparse import urlparse, parse_qs, parse_qsl

class HttpHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def process(self, method):
        url = urlparse(self.path)
        key = '%s_%s' % (method, url.path)
        if key not in self.server.routes:
            self.send_response(404)
            self.end_headers()
            return
        self.query = None
        if url.query:
            self.query = dict(parse_qsl(url.query))
        send, resp = self.server.routes[key](self)

        # handler already send body to client
        if not send:
            return

        self.send_response(resp.code)
        
        for key in resp.headers:
            self.send_header(key, resp.headers[key])
        self.end_headers()
        self.wfile.write(resp.msg.encode('utf-8'))

    def do_GET(self):
        self.process('GET')
        

    def do_POST(self):
        self.process('POST')

class ReuseAddrTCPServer(SocketServer.TCPServer):
    allow_reuse_address = True 


class HttpServer(object):
    def __init__(self, addr = '127.0.0.1', port = 19527):
        self._addr = addr
        self._port = port
        self.httpd = None
        self.routes = {}

    def start(self):
        self.httpd = ReuseAddrTCPServer((self._addr, self._port), HttpHandler) 
        self.httpd.routes = self.routes
        self.httpd.serve_forever()

    def addRoute(self, method, path, handler):
        key = '%s_%s' % (method.upper(), path)
        self.routes[key] = handler

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()

class HttpResponse(object):
    def __init__(self, msg = '', code = 200):
        self.msg = msg
        self.code = code
        self.headers = {}

    def addHeader(self, key, val):
        self.headers[key] = val

    def setBody(self, msg):
        self.msg = msg

    def setCode(self, code):
        self.code = code

