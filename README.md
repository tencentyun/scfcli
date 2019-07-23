# scf cli

------

## 什么是 scf

SCF CLI 是腾讯云无服务器云函数 SCF（Serverless Cloud Function）产品的命令行工具。通过 scf 命令行工具，您可以方便的实现函数打包、部署、本地调试，也可以方便的生成云函数的项目并基于 demo 项目进一步的开发。

scf cli通过一个函数模板配置文件，完成函数及相关周边资源的描述，并基于配置文件实现本地代码及配置部署到云端的过程。

目前 scf cli以开源形式发布，您可以在本项目中查看命令行源代码及更多帮助文档，并可以通过项目 issue 反馈问题。

## 功能特性

通过 scf 命令行工具，你可以：

* 快速初始化云函数项目
* 在本地开发及测试你的云函数代码
* 使用模拟的 COS、CMQ、Ckafka、API 网关等触发器事件来触发函数运行
* 验证 TCSAM 模板配置文件
* 打包、上传函数代码，创建函数及更新函数配置

## 运行环境

scf cli可以在 Windows、Linux、Mac 上运行。scf cli基于 Python 开发完成，因此在安装及运行前需要系统中安装有 Python 环境。更详细信息可见[安装及配置](https://github.com/tencentyun/scfcli/blob/master/docs/安装与配置.md)。

## 快速入门


### 安装 scf cli

#### 前置依赖

在安装 scf cli前，请确保系统中已经安装好了如下软件：

* Python 2.7+ 或 Python 3.6+ 
* pip
* git
* 对应的开发语言（如Node.js 8.9等）
* 腾讯云账号

#### 安装 Python 及 pip

**安装 Python**

由于 scf cli是通过使用 Python 语言开发完成的，因此在安装 scf cli前您需要先完成 Python 的安装。
您可以在 [官方下载说明页面](https://wiki.python.org/moin/BeginnersGuide/Download) 和 [官方下载地址](https://www.python.org/downloads/) 中，找到合适您的平台以及指定版本的 Python 安装程序。

> 建议您安装 Python 2.7（及以上版本）或 Python 3.6（及以上版本）。

- 针对 Windows 及 Mac 平台，您可以直接在 Python 官方网站中下载安装包，并根据普通软件的安装方式完成安装。
- 针对 Linux 平台，大部分 Linux 发行版已经内置了 Python 环境。未内置的 Linux 发行版，您可以通过包管理工具完成安装，或者通过源码进行安装。

更多详细信息请访问 [Python 官方网站](https://www.python.org/)。

**安装 pip**

完成 Python 环境的安装后，您需要安装 Python 的包管理工具 pip。通过使用 pip，您可以很方便的完整 scf 的安装、升级。
通过 [pip 官方安装指南](https://pip.pypa.io/en/stable/installing/)，可以了解到最简单的安装 pip 方法如下：

1. 执行以下命令，下载 get-pip.py 文件。

```
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
```

> 您还可以通过在线访问 get-pip.py 文件的方式，将文件保存到本地。[请点此访问 >>](https://bootstrap.pypa.io/
> get-pip.py)

1. 执行以下命令，安装 pip。

```
python get-pip.py
```

1. 执行以下命令，验证 pip 是否安装成功。

```bash
$ pip --version
```

返回类似如下信息，则表示安装成功。

```
pip 18.1 from /Library/Python/2.7/site-packages/pip (python 2.7)
```

<span id="InstallDocker"></span>



#### 通过 pip 安装 scf cli

通过使用如下命令完成 scf cli安装：

```bash
$ pip install scf
```

通过执行如下命令及输出确保 scf cli安装已成功：

```bash
$ scf --version
scf CLI, version 0.1.0
```



### 配置 scf

scf cli可配置的内容包括默认操作地域、账号 ID、账号的 SecretID 及 SecretKey。
各个配置信息的获取位置如下：

- 地域：产品期望所属的地域。地域列表及对应的英文写法可 [点此](https://cloud.tencent.com/document/product/213/6091#.E4.B8.AD.E5.9B.BD.E5.A4.A7.E9.99.86.E5.8C.BA.E5.9F.9F) 参阅。
- 账号 ID：即 APPID。通过访问控制台中的【账号中心】>【[账号信息](https://console.cloud.tencent.com/developer)】，可以查询到您的账号 ID。
- SecretID 及 SecretKey：指云 API 的密钥 ID 和密钥 Key。您可以通过登录【[访问管理控制台](https://console.cloud.tencent.com/cam/overview)】，选择【云 API 密钥】>【[API 密钥管理](https://console.cloud.tencent.com/cam/capi)】，获取相关密钥或创建相关密钥。



通过执行 `scf configure set` 命令，将获取的配置信息配置到 scf cli中。

例如获取到的账号 APPID 为 1253970223，SecretId 和 SecretKey 分别为 AKIxxxxxxxxxx 及 uxxlxxxxxxxx，期望在广州区使用云函数。

您可以通过执行以下命令，按照提示输入对应信息，完成 scf cli的配置：

```shell
$ scf configure set
TencentCloud appid(None): 1253970223
TencentCloud region(None): ap-guangzhou
TencentCloud secret-id(********************************): AKIxxxxxxxxxx
TencentCloud secret-key(****************************): uxxlxxxxxxxx
Allow report information to help us optimize scfcli(Y/n):
```

scf 也支持将参数追加在命令后进行配置【已经配置过的用户可跳过该步骤】

```bash
$ scf configure set --region ap-guangzhou --appid 1253970223 --secret-id AKIxxxxxxxxxx --secret-key uxxlxxxxxxxx
```



### 初始化模板项目

选择进入到合适的代码目录，例如 `cd ~`。

通过执行如下命令，创建运行环境为 Node.js 8.9，名称为 testscf 的函数。

```bash
$ scf init --runtime nodejs8.9 --name testscf
```

此命令会在当前目录下创建 testscf 函数目录。




### 本地触发函数

执行 `$ cd testscf` 进入函数目录。

通过执行如下命令，本地模拟触发函数。

```bash
$ scf native invoke -t template.yaml --no-event
```

注：当前仅Node.js 及Python runtime支持该能力。为保证部署云端和本地运行的结果一致，建议本地安装的runtime版本和云端版本保持一致。例如，如在云端使用Node.js 8.9，则本机建议也安装Node.js 8.x版本。




### 部署云函数

在函数目录下，通过执行如下命令，完成本地代码包及函数配置部署到云端：

```bash
$ scf deploy 
```

运行成功完成部署后，可以通过进入腾讯云云函数的控制台，检查函数是否已经成功部署。



## 详细使用指导

* [快速开始](https://github.com/tencentyun/scfcli/blob/master/docs/快速开始.md)
* [安装与配置](https://github.com/tencentyun/scfcli/blob/master/docs/安装与配置.md)
* [初始化示例项目](https://github.com/tencentyun/scfcli/blob/master/docs/初始化示例项目.md)
* [打包部署](https://github.com/tencentyun/scfcli/blob/master/docs/打包部署.md)
* [本地调试(native invoke)](https://github.com/tencentyun/scfcli/blob/master/docs/%E6%9C%AC%E5%9C%B0%E8%B0%83%E8%AF%95(native%20invoke).md)
* [本地调试(local invoke)](https://github.com/tencentyun/scfcli/blob/master/docs/%E6%9C%AC%E5%9C%B0%E8%B0%83%E8%AF%95(local%20invoke).md)
* [测试模板](https://github.com/tencentyun/scfcli/blob/master/docs/测试模板.md)
* [模板文件](https://github.com/tencentyun/scfcli/blob/master/docs/模板文件.md)
* [TCSAM说明](https://github.com/tencentyun/scfcli/blob/master/docs/specs/tencentcloud%20sam%20version%202018-11-11-zh-cn.md)
* [常见问题 FAQ](https://github.com/tencentyun/scfcli/blob/master/docs/常见问题%20FAQ.md)
