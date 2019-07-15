import os

AppID = "1259390363"
Region = "ap-hongkong"
SecretId = ""
SecretKey = ""

PythonDemoGithub = "https://github.com/tencentyun/scf-demo-python"
PythonDemoProject = "demo-python"
PythonDemoProjectPath = "./demo-python"

AppID = os.environ.get("APPID", AppID)
Region = os.environ.get("REGION", Region)
SecretId = os.environ.get("SECRET_ID", SecretId)
SecretKey = os.environ.get("SECRET_KEY", SecretKey)
PythonDemoGithub = os.environ.get("PYTHON_DEMO_GITHUB", PythonDemoGithub)
PythonDemoProject = os.environ.get("PYTHON_DEMO_PROJECT", PythonDemoProject)
PythonDemoProjectPath = os.environ.get("PYTHON_DEMO_PROJECT_PATH", PythonDemoProjectPath)