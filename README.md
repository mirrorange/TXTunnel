# TXTunnel

一个基于纯文本的隧道，用于在未开启端口转发的 SSH 服务器上，通过传输文本进行端口转发。

A tunnel based on pure text, used to forward ports through text transmission on SSH servers without port forwarding.

## 用法 Usage

若转发类型为本地，即将本地端口转发到远程端口（拨出），则在本地执行以下命令：

If the forwarding type is local, that is, the local port is forwarded to the remote port (dial-out), then execute the following command locally:

```bash
python3 client.py -s -H <host> -p <port>
```

其中，`<host>` 为服务器监听地址，`<port>` 为服务器监听端口。

其中，`<host>` is the server listening address, and `<port>` is the server listening port.

之后在目标服务器上执行以下命令：

Then execute the following command on the target server:

```bash
python3 server.py -H <host> -p <port>
```

其中，`<host>` 为转发目标地址，`<port>` 为转发目标端口。

其中，`<host>` is the forwarding target address, and `<port>` is the forwarding target port.

之后用管道或任意你喜欢的方式连接两程序的输入输出即可。

Then connect the input and output of the two programs with pipes or any way you like.

## 插件 Plugins

你可以用插件来改变 TXTunnel 输入与输出文本的方式。

You can use plugins to change the way TXTunnel inputs and outputs text.

在 plugins 目录下有一些插件的示例，stdio 是默认的插件，它使用标准输入输出来传输文本。

There are some examples of plugins in the plugins directory. stdio is the default plugin, which uses standard input and output to transmit text.

mitm 插件使用 mitmproxy 拦截网页上使用 Websocket 的 SSH 连接，使得 TXTunnel 利用网页版 SSH 客户端进行端口转发。当然，它只对特定的网页 SSH 客户端有效。

The mitm plugin uses mitmproxy to intercept SSH connections using Websocket on the webpage, so that TXTunnel can use the web SSH client for port forwarding. Of course, it is only valid for specific web SSH clients.