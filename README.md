# NJUlogin

* 南京大学统一身份认证登录模块，可用于登录校园各种网站，[Github link](https://github.com/Do1e/NJUlogin)，[PyPI link](https://pypi.org/project/NJUlogin/)。

## 安装
```bash
pip install NJUlogin -i https://mirror.nju.edu.cn/pypi/web/simple
```

注：由于使用了新的打包方式以及一些其他原因，自v3.3起，python依赖调整为`python>=3.10,<4.0`，并且在pypi上删除所有旧版包。安装旧版方法(二选一)：
* 从[Github releases](https://github.com/Do1e/NJUlogin/releases)中下载对应版本的`.whl`文件并`pip install xxx.whl`
* 克隆[Github仓库](https://github.com/Do1e/NJUlogin.git)并且checkout到对应tag的分支后使用`pip install .`安装。

## 使用
* 包含三种登录方法，**扫码登录**、**账号密码登录**、**加载cookies登录**，使用方法见[demos](demos/)文件夹

</br>

* **扫码登录**：构造`QRlogin`对象即可调用`login`方法进行登录。会在终端打印统一身份验证的二维码，使用手机扫码登录即可。(未测试字体，若出问题请尝试更换终端字体，如`MesloLGS NF`、`Fira Code`，也会在当前目录保存图片文件作为备选方案)
* **账号密码登录**：使用账号密码作为参数构造`pwdLogin`对象即可调用`login`方法进行登录。
* **加载cookies登录**：构造`baseLogin`对象即可调用`load`方法加载cookies，cookies需要通过上述两种登录方式后使用`export`方法导出为文件。`load`和`export`方法可以设置保存文件的密码防止泄露。
* `login`方法需要传入登录的目的网址，比如`https://p.nju.edu.cn/api/cas/getinfo`表示登录到校园网，返回的网页会保存在`self.response`中。目的网址也可以留空。
* 目的网址获取方法（举一反三即可）：打开浏览器输入`p.nju.edu.cn`，会发现自动跳转到`https://authserver.nju.edu.cn/authserver/login?service=https://p.nju.edu.cn/api/cas/getinfo`，即为`service=`后面的内容，。
* 返回值`session`记录了登录状态，之后即可使用`requests`中的方法进行进一步的操作，也可以使用构造出的对象调用`get`或`post`方法。（具体能有什么操作就看各位的创意了，也可以查看[我的示例](https://github.com/Do1e/p-dot-nju-login)）

<br>

方法/属性列表：
  * `login(self, dest: str = None)`：登录
  * `get(self, url: str, **kwargs) -> requests.Response`：重载了`requests.get`方法
  * `post(self, url: str, data: dict, **kwargs) -> requests.Response`：重载了`requests.post`方法
  * `logout(self)`：退出登录
  * `logout_all(self)`：退出所有设备的登录
  * `available`：判断是否登录成功
  * `export(self, filename: str, password: str = None)`：导出cookies
  * `load(self, filename: str, password: str = None)`：加载cookies

<br>

v3.4起集成了 https://p.nju.edu.cn 的登录客户端，使用方法如下：
```bash
# 安装后
NJUlogin -h
# 或者
uvx NJUlogin -h
```

```
usage: NJUlogin [-h] [-l loginlib] [-i] [-o] [-k online_id] [-p] [-a name] [-d device_id]

options:
  -h, --help            show this help message and exit
  -l, --loginlib loginlib
                        登录库，QRlogin或pwdLogin，默认为QRlogin
  -i, --login           登录
  -o, --logout          登出
  -k, --kick online_id  登出指定在线设备，使用`-p`可获取online_id
  -p, --printinfo       打印信息
  -a, --add name        添加当前设备为无感认证设备，name为设备名称
  -d, --delete device_id
                        删除无感认证设备，指定设备ID，使用`-p`可获取device_id
```

## 补充
* 这个项目很难进行完整的测试，毕竟难以预测所有的网络情况，而且网站的登录方式也会有更新，因此欢迎大家提出issue，我会尽力解决（只要我还在南大）。

## 致谢
* 验证码识别代码来自[sml2h3/ddddocr](https://github.com/sml2h3/ddddocr)
