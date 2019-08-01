import os
import time

appid = "100005358439"
secretid = "AKID1ynRAoVcoqrDUbwR9RbcS7mKrOl1q0kK"
secretkey = "cCoJncN0BHLG2jGvcAYlXWRI5kFZj5Oa"
region_list = ['ap-beijing', 'ap-chengdu', 'ap-guangzhou', 'ap-hongkong', 'ap-mumbai', 'ap-shanghai']
runtime_list = ["python3.6", "python2.7", "go1", "php5", "php7", "nodejs6.10", "nodejs8.9"]

command_dict = {
    "configure": {
        "帮助功能": [
            "scf configure --help",
            "scf configure set --help",
            "scf configure get --help",
            "scf delete --help",
            "scf deploy --help",
            "scf init --help",
            "scf list --help",
            "scf local --help",
            "scf local generate-event --help",
            "scf local generate-event apigateway --help",
            "scf local generate-event ckafka --help",
            "scf local generate-event cmq --help",
            "scf local generate-event cos --help",
            "scf local generate-event timer --help",
            "scf local invoke --help",
            "scf logs --help",
            "scf native --help",
            "scf native generate-event --help",
            "scf native invoke --help",
            "scf native start-api --help",
            "scf validate --help",
        ],
        "设置": [
            "scf configure get",
            "scf configure get --aaaa",
            "scf configure get --appid",
            "scf configure get --region",
            "scf configure get --secret-id",
            "scf configure get --secret-key",
            "scf configure get --using-cos",
        ]
    }
}

for eve_key, eve_value in command_dict.items():
    print("测试模块：%s" % eve_key)
    for eve_command_name, eve_command in eve_value.items():
        print("测试内容：%s" % eve_command_name)
        print("测试结果：")
        for eve in eve_command:
            os.system(eve)
            print("-" * 100)
        print("=" * 100)
        time.sleep(2)
