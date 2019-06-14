通过本地调试能力，scf CLI可以在本地的模拟环境中运行代码，发送模拟测试事件，并获取到函数代码的运行日志及耗时、内存占用等信息。

## Dependent component

Local debugging native does not need to rely on Docker and ensure that the Node.js environment is already installed on the system. The current native command only supports Node.js and Python runtime. To ensure consistent deployment of the cloud and the local version, it is recommended that the local version of the runtime and the cloud version be the same. For example, if you are using Node.js 6.10 in the cloud, this machine is also recommended to install Node.js 6.x.

## Debug command

scf cli通过 `native invoke` 子命令完成本地触发运行。scf 命令行工具将依据指定的函数模板配置文件，在本机的指定目录中运行相应代码，并通过指定的触发事件，实现在本地的云函数模拟运行。

### Parameter Description

The parameters supported by the `scf native invoke` command are as follows:

参数 | Required | 描述 | Example
--- | --- | --- | ---
Event | no | The source of the file for the simulated test event, the file content must be in JSON format | Event.json
Template | no | 项目描述配置文件的路径或文件名。默认为 template.yaml | Template.yaml
Env-vars | no | The environment variable configuration when the function is running, you need to specify the environment variable configuration file, the content must be in JSON format. | Env.json
Debug-port | no | The port exposed when the function is running. After the port is specified, the local runtime will start in debug mode and expose the specified port. | 3366
Debug-args | no | The debugger startup parameters in this machine. After the parameter is specified, the specified parameters will be passed when the debugger starts. | 

The support option FUNCTION_IDENTIFIER is described as follows:

参数 | Required | 描述 | Example
--- | --- | --- | ---
FUNCTION_IDENTIFIER | no | Indicates the identifier and name of the function; if there are multiple function descriptions in the project description configuration file, you can use this parameter to specify the function to be debugged. | Hello_world

### Test simulation event

The simulation event used to trigger the cloud function locally can be passed through the command pipeline of linux or passed through a file.

- **通过命令管道传递：** `scf native invoke` 命令支持从命令行管道中接收事件。我们可以通过执行 `scf native generate-event` 命令生成事件并传递，形成例如 `scf native generate-event cos post | scf native invoke --template template.yaml` 的调试命令。我们也可以自行构造输出 JSON 格式内容并传递给 `scf native invoke` 命令，形成例如 `echo '{"test":"value"}' | scf native invoke --template template.yaml` 的调试命令。
- **通过文件传递：**通过使用 `scf native invoke` 命令的 `--event` 参数，指定包含有测试模拟事件内容的文件。文件内容必须为 JSON 数据结构，形成例如 `scf native invoke --template template.yaml --event event.json` 的调试命令。

### Use example

The sample project that was initialized by `scf init` has the prepared code file and template configuration file. Taking the example project as an example, assume that a hello_world project is created in the /Users/xxx/code/scf directory under the environment Node.js 8.9.

We pass the simulation event of the cos post file through the command pipeline, triggering the function to run. The function code content only prints the event and returns "hello world". The function code /Users/xxx/code/scf/testproject/hello_world/main.js is as follows:

```

'use strict';
exports.main_handler = async (event, context, callback) => {
    console.log("%j", event);
    return "hello world"
};

```

1. The startup function runs locally by executing the `scf native generate-event cos post | scf native invoke --template template.yaml` command:

```bash
Enter a event: [0m
START RequestId: 3e3e71c9-dc56-1967-c0a3-3a454e2ce634
{"Records":[{"cos":{"cosSchemaVersion":"1.0","cosObject":{"url":"http://testpic-1253970026.cos.ap-guangzhou.myqcloud.com/testfile","meta":{"x-cos-request-id":"NWMxOWY4MGFfMjViMjU4NjRfMTUyMV8yNzhhZjM=","Content-Type":""},"vid":"","key":"/1253970026/testpic/testfile","size":1029},"cosBucket":{"region":"gz","name":"testpic","appid":"1253970026"},"cosNotificationId":"unkown"},"event":{"eventName":"cos:ObjectCreated:Post","eventVersion":"1.0","eventTime":1545205770,"eventSource":"qcs::cos","requestParameters":{"requestSourceIP":"xx.xx.xx.xxx","requestHeaders":{"Authorization":"q-sign-algorithm=sha1&q-ak=AKIDQm6iUh2NJ6jL41tVUis9KpY5Rgv49zyC&q-sign-time=1545205709;1545215769&q-key-time=1545205709;1545215769&q-header-list=host;x-cos-storage-class&q-url-param-list=&q-signature=098ac7dfe9cf21116f946c4b4c29001c2b449b14"}},"eventQueue":"qcs:0:lambda:cd:appid/1253970026:default.printevent.$LATEST","reservedInfo":"","reqid":179398952}}]}
END RequestId: 3e3e71c9-dc56-1967-c0a3-3a454e2ce634
REPORT RequestId: 3e3e71c9-dc56-1967-c0a3-3a454e2ce634  Duration: 1.91 ms
Billed Duration: 100 ms Memory Size: 128 MB     Max Memory Used: 20 MB
"hello world"
```

As you can see from the output, after the function finishes running locally, it outputs the print log of the function and the function return content.

1. Generate the following event.json test event file:

```json
{
"key1":"value1",
"key2":"value2"
}
```

1. By executing the `scf native invoke --template template.yaml --event event.json` command, the startup function runs locally and outputs test events via a file:

```bash
Enter a event: [0m
START RequestId: 6d06b0cf-4cc9-1f76-5f92-1f5871ff110a
{"key1":"value1","key2":"value2"}

END RequestId: 6d06b0cf-4cc9-1f76-5f92-1f5871ff110a
REPORT RequestId: 6d06b0cf-4cc9-1f76-5f92-1f5871ff110a  Duration: 1.72 ms
Billed Duration: 100 ms Memory Size: 128 MB     Max Memory Used: 20 MB

"hello world"
```

As you can see from the output, the function code prints the test event and returns the specified content.
