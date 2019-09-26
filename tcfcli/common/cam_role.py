from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cam.v20190116 import cam_client, models
from tcfcli.common.user_config import UserConfig
import json


def list_scf_role(region):
    try:
        uc = UserConfig()
        region = region if region else uc.region
        cred = credential.Credential(uc.secret_id, uc.secret_key)
        httpProfile = HttpProfile()
        httpProfile.endpoint = "cam.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = cam_client.CamClient(cred, region, clientProfile)

        req = models.DescribeRoleListRequest()
        params = '{"Page":1,"Rp":200}'
        req.from_json_string(params)

        resp = client.DescribeRoleList(req)
        data = json.loads(resp.to_json_string())
        rolelist = []
        for role in data['List']:
            for state in json.loads(role['PolicyDocument'])['statement']:
                if 'service' in state['principal'] and 'scf.qcloud.com' in state['principal']['service']:
                    rolelist.append(str(role['RoleName']))
                    continue
        return rolelist
    except Exception as e:
        # print(e)
        return None