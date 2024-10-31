import base64
import http.client
import http.server
import socket
import socketserver
import ssl
import urllib

# pip install scapy
from scapy.all import *

load_layer('tls')
conf.logLevel = logging.INFO

# 代理服务器的地址和端口
proxy_address = ('0.0.0.0', 3128)

USERNAME = 'sam'
PASSWORD = '12345678'

class ProxyHandler(http.server.SimpleHTTPRequestHandler):

  def auth_www(self):
    # 检查认证信息
    if 'Authorization' not in self.headers:
      self.send_response(401)
      self.send_header('WWW-Authenticate', 'Basic realm="Proxy"')
      self.end_headers()
      return False
    if not (self.headers['Authorization'] == f'Basic {base64.b64encode(f"{USERNAME}:{PASSWORD}".encode("utf-8")).decode("utf-8")}'):
      # 认证失败，返回403
      self.send_response(403)
      self.end_headers()
      return False
    return True

  def auth(self):
    # 检查认证信息
    if 'Proxy-Authorization' not in self.headers:
      self.send_response(407)
      self.send_header('Proxy-Authenticate', 'Basic realm="Proxy"')
      self.end_headers()
      return False
    if not (self.headers['Proxy-Authorization'] == f'Basic {base64.b64encode(f"{USERNAME}:{PASSWORD}".encode("utf-8")).decode("utf-8")}'):
      # 认证失败，返回403
      self.send_response(403)
      self.end_headers()
      return False
    return True

  def do_GET(self):
    # 检查认证信息
    if not self.auth():
      return
    # 这里可以对GET请求进行拦截和处理
    # print("do_GET")
    u = urllib.parse.urlparse(self.path)
    print("GET path=%s" % self.path)
    conn = http.client.HTTPConnection(u.hostname, u.port or 80)
    conn.request("GET", url=u.path, headers=self.headers)
    res = conn.getresponse()
    self.send_response(res.getcode())
    for title in res.headers:
      self.send_header(title, res.headers[title])
    self.end_headers()
    data = res.read()
    # self.wfile.write(data) #也可以
    self.connection.sendall(data)
    self.connection.close()

  def do_POST(self):
    # 检查认证信息
    if not self.auth():
      return
    # 这里可以对POST请求进行拦截和处理
    # print("do_POST")
    u = urllib.parse.urlparse(self.path)
    print("POST path=%s" % self.path)

    body = self.rfile.read(int(self.headers['content-length']))  # 重点在此步!
    print(body.decode())

    conn = http.client.HTTPConnection(u.hostname, u.port or 80)
    conn.request("POST", url=self.path, body=body.decode(), headers=self.headers)
    res = conn.getresponse()
    self.send_response(res.getcode())
    for title in res.headers:
      self.send_header(title, res.headers[title])
    self.end_headers()
    data = res.read()
    # self.wfile.write(data) #也可以
    self.connection.sendall(data)
    self.connection.close()

  def do_PUT(self):
    print("do_PUT")
    pass

  def do_DELETE(self):
    print("do_DELETE")
    pass

  def do_HEAD(self):
    print("do_HEAD")
    pass

  def do_OPTIONS(self):
    print("do_OPTIONS")
    pass

  def do_CONNECT(self):
    # 检查认证信息
    if not self.auth():
      return

    # 响应客户端
    self.connection.setblocking(False)
    self.connection.sendall(b'HTTP/1.1 200 Connection Established\n\n')

    # 创建目标服务器连接
    u = urllib.parse.urlparse('http://' + self.path)
    print("CONNECT path=%s" % self.path)
    forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    timeout = 1
    forward_socket.settimeout(timeout)
    forward_socket.connect((u.hostname, u.port or 80))
    forward_socket.setblocking(False)

    # # 很多网站使用了hsts，这段代码说明无法冒充目标网站进行拦截，也就无法在中间修改，因为浏览器会返回异常，net::ERR_CERT_AUTHORITY_INVALID。
    # self.connection.setblocking(True)
    # context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # context.load_cert_chain('./certificate.pem', './private_key.pem')
    # connection = context.wrap_socket(self.connection, server_side=True)

    # 客户端和目标服务器交换TLS加密数据（代理服务器是解不开的）
    # 建立隧道后，请求是由目标服务器完成，而不是代理服务器完成的
    while True:
      try:
        # 从客户端接收数据
        data1 = self.connection.recv(1024)
        if not data1:
          break
        forward_socket.sendall(data1)
        record1 = TLS(data1[:])
        sess = record1.tls_session
        print("---------------- Client ----------------")
        # 展示从客户端接收的数据，不用时可以注释掉
        record1.show()
        # print(repr(data1))
      except Exception as e1:
        pass
      try:
        # 从目标服务器接收数据
        data2 = forward_socket.recv(1024)
        if not data2:
          break
        self.connection.sendall(data2)
        record1 = TLS(data2[:])
        sess = record1.tls_session
        print("---------------- Server ----------------")
        # 展示从目标服务器接收的数据，不用时可以注释掉
        record1.show()

      except Exception as e2:
        pass

    self.connection.close()
    forward_socket.close()

  def do_TRACE(self):
    # 这里可以对TRACE请求进行拦截和处理
    print("do_TRACE")
    pass


# with socketserver.TCPServer(proxy_address, ProxyHandler) as httpd:
if __name__ == '__main__':
  with socketserver.ThreadingTCPServer(proxy_address, ProxyHandler) as httpd:
    print(f'Starting HTTP proxy server at {proxy_address[0]}:{proxy_address[1]}')
    httpd.serve_forever()
