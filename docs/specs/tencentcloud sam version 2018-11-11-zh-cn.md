# Tencent Cloud Serverless Application Model

##### 版本 2018-11-11

本文件中的 “一定”，“不一定”，“必填”，“将要”，“最好不要”，“应该”，“不应该”，“推荐”，“可能”，和 “可选” 按照 [RFC 2119](http://www.ietf.org/rfc/rfc2119.txt) 中的描述进行解释。

Tencent Cloud Serverless Application Model 根据 [Apache 2.0 许可证](http://www.apache.org/licenses/LICENSE-2.0.html) 授权。

## 介绍

TCSAM 是用于在腾讯云上定义 Serverless 应用的模型。

Serverless 应用是由事件触发运行的应用。一个典型的 serverless 应用由一个或多个腾讯云无服务器云函数 SCF 组成，云函数由例如向 [腾讯云对象存储 COS](https://cloud.tencent.com/product/cos) 上传对象文件操作、向 [腾讯云消息队列 CMQ](https://cloud.tencent.com/product/mq) 中投递消息等事件触发。这些函数可以独立运行，也可以使用其它资源，例如腾讯云对象存储 COS，腾讯云数据库服务 CDB。最基本的 serverless 应用可以只有一个函数。

## 规范

### 格式

腾讯云 TCSAM 用通过 [YAML](http://yaml.org/spec/1.1/) 或 [JSON](http://www.json.org/) 格式的模板文件来描述 serverless 应用。

- [资源类型](#resource-type)
- [事件源类型](#event-source-type)
- [属性类型](#property-type)
- [全局部分](#global-section)

### 示例：腾讯云 TCSAM 模板

```yaml
Resources:
  ProjectTest: # namespace name
    Type: 'TencentCloud::Serverless::Namespace'
    TestFunction: # function name
      Type: 'TencentCloud::Serverless::Function'
      Properties:
        Handler: index.handler
        Runtime: Python2.7
        CodeUri: './' 
      Events:
        crontrigger: # trigger name
          Type: timer # api gateway trigger
          Properties:
              Cron: '*/5 * * * *'
```

腾讯云 TCSAM 中的所有属性名称都**区分大小写**。

<span id = "global-section"></span>
### 全局部分

全局部分定义了 TCSAM 模板中的全局属性，这些属性会被 `TencentCloud::Serverless::Function` 、 `TencentCloud::Serverless::Api` 资源继承。

案例：

```yaml
Globals:
  Function:
    Runtime: Python2.7
    Timeout: 30
    Handler: index.handler
    Environment:
      Variables:
        DB_NAME: mydb
```

<span id = "resource-type"></span>
### 资源类型

- [TencentCloud::Serverless::Namespace](#tencentcloudserverlessnamespace)
  - [TencentCloud::Serverless::Function](#tencentcloudserverlessfunction)
- [TencentCloud::Serverless::Api](#tencentcloudserverlessapi)


#### TencentCloud::Serverless::Namespace

无服务器云函数 SCF 命名空间。命名空间由一组函数组成。

#### TencentCloud::Serverless::Function

描述无服务器云函数以及触发该函数的事件源。云函数属于某个命名空间。

###### 属性

属性名称 | 类型 | 描述
---|:---:|---
Handler | `string` | **必填。** 云函数的入口执行方法。
Runtime | `string` | **必填。** 云函数的运行时环境。可选值为：Python2.7、Python3.6、Nodejs6.10、Nodejs8.9、Nodejs10.15、Nodejs12.16、Php5、Php7、Golang1、Java8。
CodeUri | `string` | **必填。** 代码位置。支持本地文件、本地目录、本地 zip 文件、对象存储 COS bucket 及 object 等形式，更多信息参考[Codeuri](#CodeUri)。
Description | `string` | 云函数的描述。
MemorySize | `integer` | 函数执行时分配的内存大小，单位是 MB，默认为 128（MB），按 128 递增。
Timeout | `integer` | 函数在被终止之前可以运行的最长时间，单位是秒，默认为 3 秒。
Role | `string`| 通过填写角色名称，为函数指定运行角色。 如果此字段缺省，将为函数创建一个默认的角色QCS_SCFExcuteRole。
Policies | `string`&#124;`string`列表&#124;[CAM Policy文档对象](https://cloud.tencent.com/document/product/598/10603)&#124;CAM Policy文档对象列表 | 指定函数需要的CAM预设策略名称，或自定义策略。如Role为默认角色或缺省，则策略会被附加到该函数的默认角色上。如果设置了自定义的Role属性，则Policies属性会被忽略。
Environment | [环境变量对象](#环境变量对象) | 为函数配置[环境变量](https://cloud.tencent.com/document/product/583/30228)。
Events | [事件源对象](#事件源对象) | 用于定义触发此函数的事件源。
VpcConfig | [VPC配置对象](#Vpc配置对象) | 用于配置云函数访问 VPC 私有网络。

##### 示例：TencentCloud::Serverless::Namespace 与 TencentCloud::Serverless::Function

```yaml

ProjectTest: # 命名空间名称
  Type: 'TencentCloud::Serverless::Namespace'
  TestFunction: # 函数名
    Type: 'TencentCloud::Serverless::Function'
    Properties:
      Handler: index.handler
      Runtime: Python2.7
      CodeUri: './'
      Description: Cron function
      Role: QCS_SCFExcuteRole
      Timeout: 10
      MemorySize: 512
      
```

<span id = "event-source-type"></span>
### 事件源类型

- [Timer](#timer)
- [COS](#cos)
- [API](#api)
- [CMQ](#cmq)
- [CKafka](#ckafka)

#### Timer

描述类型为[定时触发器](https://cloud.tencent.com/document/product/583/9708)的对象。

##### 属性

属性名称 | 类型 | 描述
---|:---:|---
CronExpression | `string` | **必填。** 函数被触发的时间，支持指定的 [cron 表达式](https://cloud.tencent.com/document/product/583/9708#cron-.E8.A1.A8.E8.BE.BE.E5.BC.8F)。
Enable | `boolean` | 是否启用触发器。

##### 示例：Timer 事件源对象

```yaml
Type: Timer
Properties:
  CronExpression: '*/5 * * * *'
  Enable: true
```

#### COS

描述类型为[对象存储触发器](https://cloud.tencent.com/document/product/583/9707)的对象。

##### 属性

属性名称 | 类型 | 描述
---|:---:|---
Bucket | `string` | **必填.** COS 对象存储存储桶 bucket 名称。
Events | `string` | **必填.** 触发云函数的事件，可选值为 `cos:ObjectCreated:*`、`cos:ObjectCreated:Put`、`cos:ObjectCreated:Post`、`cos:ObjectCreated:Copy`、`cos:ObjectCreated:Append`、`cos:ObjectCreated:CompleteMultipartUpload`、`cos:ObjectRemove:*`、`cos:ObjectRemove:Delete`、`cos:ObjectRemove:DeleteMarkerCreated`
Filter | [COS 通知过滤器](#cos通知过滤) | 触发事件的过滤器规则。
Enable | `boolean` | 是否启用触发器。

##### 示例：COS 事件源对象

```yaml
Type: COS
Properties:
  Bucket: mycosbucket
  Events: cos:ObjectCreated:*
  Filter:
    Prefix: 'filterdir/'
    Suffix: '.jpg'
  Enable: true
```

#### API

描述类型为 [API 网关触发器](https://cloud.tencent.com/document/product/583/12513) 的对象。

如果在描述文件中同时存在 [API 资源对象](#tencentcloudserverlessapi) 和 [API网关触发器事件源对象](#api) 时，API 资源对象将生效。

##### 属性

属性名称 | 类型 | 描述
---|:---:|---
StageName | `string` | 发布阶段的名称，API网关用作调用统一资源标识符（URI）中的第一个路径段。可选值为：test、prepub、release。默认如果为新 API 服务时为 release，已有 API 服务时为 test。
HttpMethod | `string`  | HTTP 请求方法，可选值为：ANY、GET、POST、PUT、DELETE、HEAD。默认值为 ANY。
IntegratedResponse | `boolean`  | 是否启用集成响应。默认值为 false。
Enable | `boolean` | 是否启用触发器。

##### 示例：API 事件源对象

```yaml
apigw-trigger: # api gateway service name
    Type: APIGW # trigger type
    Properties:
        StageName: release
        HttpMethod: ANY
        IntegratedResponse: true
        Enable: true
```

#### CMQ

描述类型为 [CMQ 消息队列触发器](https://cloud.tencent.com/document/product/583/11517) 的对象。

##### 属性

属性名称 | 类型 | 描述
---|:---:|---
Name | `string` | **必填。** 消息队列名称。
Enable | `boolean` | 是否启用触发器。

##### 示例：CMQ 事件源对象

```yaml
Events:
  Type: CMQ
  Properties:
    Name: test-topic-queue
    Enable: true
```
#### CKafka

描述类型为 [CKafka 触发器](https://cloud.tencent.com/document/product/583/17530) 的对象。

##### 属性

属性名称 | 类型 | 描述
---|:---:|---
Name | `string` | **必填。** 消息队列CKafka名称。
Topic | `string` | **必填。** 消息队列CKafka主题Topic名称。
MaxMsgNum | `integer` | **必填。** 最大批量消息数，范围1-1000。
Offset | `string` | 起始offset位置，默认为latest。
Enable | `boolean` | 是否启用触发器。

##### 示例：CKafka 事件源对象

```yaml
Events:
  Type: Ckafka
  Properties:
    Name: ckafka-2o10hua5
    Topic: test
    MaxMsgNum: 999
    Offset: latest
    Enable: true
```

<span id = "property-type"></span>
### 属性类型

- [事件源对象](#事件源对象)
- [VPC 配置对象](#Vpc配置对象)
- [环境变量对象](#环境变量对象)

#### 事件源对象

描述触发函数的事件源的对象。

##### 属性

属性名称 | 类型 | 描述
---|:---:|---
Type | `string` | **必填。** 事件类型。 事件源类型包括 [Timer](#timer)、[COS](#cos)、[Api](#api)、[CMQ](#cmq) 。有关所有类型的更多信息， 请参阅 [事件源类型](#事件源类型)。
Properties | * | **必填。** 描述此事件映射属性的对象。必须符合定义的 `类型` 。有关所有类型的更多信息，请参阅 [事件源类型](#事件源类型)。

##### 示例：事件源对象

```yaml
Events:
  Type: Timer
  Properties:
    CronExpression: '*/5 * * * *'
    Enable: true
```


#### Vpc 配置对象

Vpc 配置对象包含的属性包括： `VpcId`、`SubnetId` 属性。它们所代表的含义参考 [VPC Config 对象](https://cloud.tencent.com/document/api/583/17244#VpcConfig)。

属性名称 | 类型 | 描述
---|:---:|---
VpcId | `string` | **必填。** VPC私有网络 ID 。
SubnetId | `string` | **必填。** 属于 VPC 内的子网 ID。


##### 示例：VPC 配置对象

```
VpcConfig:
  VpcId: 'vpc-qdqc5k2p'
  SubnetId: 'subnet-pad6l61i'
```


#### 环境变量对象

环境变量对象描述了函数可以配置的环境变量属性，环境变量配置为一系列的键值对。

属性名称 | 类型 | 描述
---|:---:|---
Variables | `string` 到 `string` 的映射 | 定义环境变量的字符串对字符串映射，其中变量名为 key，变量值为 value。变量名限制为字母与数字组合，且第一个字符需要为字母。变量值定义为字母与数字及特殊字符 `_(){}[]$*+-\/"#',;.@!?` 的组合。

##### 示例：环境变量对象

```
Environment:
  Variables:
    MYSQL_USER: root
    MYSQL_PASS: pass
```

### 数据类型

- [COS 对象](#cos-object)
- [Code URI 对象](#codeuri-object)
- [COS 通知过滤](#cos-filter)


<span id = "cos-object"></span>
#### COS对象

通过指定`Bucket`、`Key` 指定对象存储位置，用于指向代码存储位置。

案例：

```yaml
CodeUri:
  Bucket: mycodebucket
  Key: '/code.zip'
```

<span id = "codeuri-object"></span>
#### CodeUri

CodeUri 用来指定代码存储的位置，可以指定为本地文件系统中的文件、文件夹、zip 包或对象存储 COS 中的内容。

案例：

```yaml
CodeUri: index.py
```

```yaml
CodeUri: ./build
```

```yaml
CodeUri: /user/code/func/build.zip
```

<span id = "cos-filter"></span>
#### COS通知过滤

用于指定对象存储通知时的过滤配置，由前缀过滤参数和后缀过滤参数组合而成。

案例：

```yaml
Filter:
  Prefix: 'filterdir/'
  Suffix: '.jpg'
```
