import os
import platform
import re
import subprocess
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST_NAME = "0.0.0.0"
PORT_NUMBER = 80


def memory():
    with open('/proc/meminfo', 'r') as mem:
        ret = {}
        tmp = 0
        for i in mem:
            sline = i.split()
            if str(sline[0]) == 'MemTotal:':
                ret['total'] = int(sline[1])
            elif str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                tmp += int(sline[1])
        ret['free'] = tmp
        ret['used'] = int(ret['total']) - int(ret['free'])
    return ret


def uptime():
    with open('/proc/uptime', 'r') as up:
        return next(up).split()[0]


def cpu_model():
    command = "cat /proc/cpuinfo"
    all_info = subprocess.check_output(command, shell=True).decode().strip()
    for line in all_info.split("\n"):
        if "model name" in line:
            return re.sub(".*model name.*:", "", line, 1)


def cpu_usage():
    return str(round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage }' ''').readline()),2))


def processes():
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    res = {}

    for pid in pids:
        try:
            command = f'cat /proc/{pid}/cmdline'
            name = subprocess.check_output(command, shell=True).decode().strip()
            res[pid] = name
        except subprocess.CalledProcessError:
            continue

    return res


class MyHandler(BaseHTTPRequestHandler):
    def create_content(self):
        mem = memory()
        mem_total = mem['total']
        mem_used = mem['used']
        content = f"""
        <html>
            <head><title>Info do sistema</title></head>
            <body>
                <p>Data e Hora: {datetime.now()}</p>
                <p>Uptime (s): {uptime()}</p>
                <p>Modelo e velocidade do CPU: {cpu_model()}</p>
                <p>Uso do CPU (%): {cpu_usage()}</p>
                <p>Memoria RAM total (MB): {mem_total / (1024.0 ** 2)}</p>
                <p>Memoria RAM usada (MB): {mem_used / (1024.0 ** 2)}</p>
                <p>Versao do sistema: {platform.platform()}</p>
                <p>Processos em execucao:</p>
                <ul>
        """

        for pid, name in processes().items():
            content += f'<li>{pid} {name}</li>\n'

        content += """
                </ul>
            </body>
        </html>
        """
        return content.encode()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(self.create_content())


if __name__ == "__main__":
    httpd = HTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
    print("Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))
