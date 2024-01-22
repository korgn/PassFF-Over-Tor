#!/usr/bin/python3
"""
    Host application of the browser extension PassFF
    that wraps around the zx2c4 pass script.
"""

import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO

VERSION = "1.2.4"

###############################################################################
######################## Begin preferences section ############################
###############################################################################
COMMAND = "/usr/bin/pass"
COMMAND_ARGS = []
COMMAND_ENV = {
    "TREE_CHARSET": "ISO-8859-1",
    "PATH": "/home/su/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/snap/bin:/home/su/.dotnet/tools:/opt/jadx/bin"
}
CHARSET = "UTF-8"

###############################################################################
######################### End preferences section #############################
###############################################################################

class RequestHandler(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data.decode('utf-8'))
    
        data = payload.get('args', [])

        opt_args = []
        pos_args = []
        std_input = None

        if len(data) == 0:
            opt_args = ["show"]
            pos_args = ["/"]
            print("Len data 0")
        elif data[0] == "insert":
            opt_args = ["insert", "-m"]
            pos_args = [data[1]]
            std_input = data[2]
            print("ins")
        elif data[0] == "generate":
            opt_args = ["generate"]
            pos_args = [data[1], data[2]]
            if "-n" in data[3:]:
                opt_args.append("-n")
            print("gen")
        elif data[0] == "grepMetaUrls" and len(data) == 2:
            opt_args = ["grep", "-iE"]
            url_field_names = data[1]
            pos_args = ["^({}):".format('|'.join(url_field_names))]
            print("GMU")
        elif data[0] == "otp" and len(data) == 2:
            opt_args = ["otp"]
            key = data[1]
            key = "/" + (key[1:] if key[0] == "/" else key)
            pos_args = [key]
        else:
            opt_args = ["show"]
            key = data[0]
            key = "/" + (key[1:] if key[0] == "/" else key)
            pos_args = [key]
            print("show")
        opt_args += COMMAND_ARGS

        env = dict(os.environ)
        if "HOME" not in env:
            env["HOME"] = os.path.expanduser('~')
        for key, val in COMMAND_ENV.items():
            env[key] = val

        cmd = [COMMAND] + opt_args + ['--'] + pos_args
        proc_params = {
            'input': bytes(std_input, CHARSET) if std_input else None,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'env': env
        }

        proc = subprocess.run(cmd, **proc_params)

        response = {
            "exitCode": proc.returncode,
            "stdout": proc.stdout.decode(CHARSET),
            "stderr": proc.stderr.decode(CHARSET),
            "version": VERSION
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=RequestHandler, port=5000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}')
    httpd.serve_forever()

if __name__ == "__main__":
    run()