# forward-proxy

## 说明

在配置Nginx作为前向代理时，我们遇到了一个令人困扰的问题：许多知名网站，如谷歌、Huggingface、YouTube等，无法正常访问。深入探究后，我们发现，通过代理访问HTTPS网站时，会经历一个特定的过程，即首先建立连接，随后代理服务器作为客户端与目标服务器之间的中间人，进行无改动的数据传输。这一过程被称为“隧道”（tunnel）。

forward-proxy.py作为一个简单的前向代理，也可以说明以上问题。

## 使用

### 服务端

```shell
python forward-proxy.py
```

### 客户端

#### HTTP

##### GET

```shell
curl -x 127.0.0.1:3128 https://www.baidu.com
```

##### POST

```shell
curl -x 127.0.0.1:3128 --request POST \
  --url 'http://10.200.60.99:8080/api/settings?role_name=mila' \
  --header 'Authorization: Basic c2FtOjEyMzQ1Ng==' \
  --header 'Content-Type: application/json' \
  --header 'User-Agent: insomnia/9.3.2' \
  --cookie user_id=b9d6a3f-64ad-42c5-9de0-bb0eefcf3cb7 \
  --data '{
	"model": "qwen2.5:7b-instruct",
	"descript": "https://qwenlm.github.io/blog/qwen2.5/",
	"options": {
    "temperature": 0.1,
    "top_k": 70,
    "top_p": 0.8,
    "repetition_penalty": 1,
    "max_tokens": 32768
  },
	"stream": true,
	"messages": [
		{
			"role": "system",
			"content": "。。。"
		},
		{
			"role": "user",
			"content": "。。。"
		}
	]
}'

```

#### HTTPS

##### CONNECT

```shell
curl -x 127.0.0.1:3128 https://www.baidu.com
```

## 参考

### 代理服务器

代理服务器是一种位于客户端和目标服务器之间的中间服务器。它接收来自客户端的请求，并将其转发给目标服务器。同样，它也接收来自目标服务器的响应，并将其返回给客户端。通过这种方式，代理服务器可以隐藏客户端的真实IP地址，提供访问控制、缓存、日志记录等功能。

### 隧道

在HTTPS通信中，由于数据是加密的，代理服务器无法直接读取或修改这些数据。因此，当客户端通过代理服务器访问HTTPS网站时，会建立一个隧道。这个隧道允许加密的数据流在客户端和目标服务器之间安全地传输，而无需代理服务器对其进行解密或修改。

隧道的建立过程如下：

1. 客户端向代理服务器发送一个HTTPS请求。
2. 代理服务器接收到请求后，与目标服务器建立一个HTTPS连接。
3. 在这个连接中，代理服务器会向目标服务器传递客户端的原始请求（包括加密的数据）。
4. 目标服务器处理请求后，将加密的响应通过代理服务器返回给客户端。

### 某些网站无法正常工作的原因

尽管隧道机制确保了HTTPS通信的安全性，但它也可能导致某些网站无法正常工作。这主要有以下几个原因：

1. **SSL/TLS证书验证失败**：当代理服务器与目标服务器建立HTTPS连接时，它们会进行SSL/TLS握手。如果代理服务器的SSL/TLS配置不正确（例如，证书不受信任或过期），则可能导致握手失败，从而使网站无法访问。
2. **HSTS（HTTP Strict Transport Security）策略**：某些网站实施了HSTS策略，要求客户端只能通过HTTPS访问它们。如果代理服务器没有正确配置以支持HTTPS隧道，或者客户端的HTTPS请求被代理服务器以某种方式修改（尽管在隧道中不应发生这种情况），则可能导致HSTS策略阻止访问。
3. **地理限制和IP封锁**：一些网站会根据用户的地理位置或IP地址来限制访问。如果代理服务器的IP地址位于被封锁的区域内，或者与某些恶意行为相关联，则可能导致网站无法访问。
4. **代理服务器配置问题**：如果代理服务器的配置不正确（例如，端口转发规则错误、超时设置不合理等），也可能导致网站无法正常工作。
