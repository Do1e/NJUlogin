# NJUlogin

* 南京大学统一身份认证登录模块，可用于登录校园各种网站

## 安装
```bash
python setup.py install
```
或者  
```bash
pip install NJUlogin
```

## 使用
* 目前暂时只支持扫码登录，后续将会添加账号密码登录
* 使用方法见`demos`文件夹

### 扫码登录
* 构造`QRlogin`对象即可调用`login`方法进行登录。
* 需要传入登录的目的网址，比如`http://p.nju.edu.cn/cas/&renew=true`表示登录到校园网。
* 获取方法（举一反三即可）：打开浏览器输入`p.nju.edu.cn`，会发现自动跳转到`https://authserver.nju.edu.cn/authserver/login?service=http%3A%2F%2Fp.nju.edu.cn%2Fcas%2F&renew=true`，即为`service=`后面的内容，这里经过了编码，不解码直接作为目的地址传入也可以。
* 返回值`session`记录了登录状态，之后即可使用`requests`中的方法进行进一步的操作。（具体能有什么操作就看各位的创意了，也可以查看[我的示例](https://github.com/Do1e/p-dot-nju-login)）
* 注：会在终端打印统一身份验证的二维码，使用手机扫码登录即可。(未测试字体，若出问题请尝试更换终端字体，如`MesloLGS NF`、`Fira Code`)

## 补充
* 这个项目很难进行完整的测试，毕竟难以预测所有的网络情况，而且网站的登录方式也会有更新，因此欢迎大家提出issue，我会尽力解决（只要我还在南大）。