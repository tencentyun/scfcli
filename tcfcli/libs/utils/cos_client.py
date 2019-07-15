import xmltodict
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from tcfcli.common.user_config import UserConfig
from tcfcli.common.user_exceptions import UploadToCosFailed


class CosClient(object):
    def __init__(self, region=None):
        uc = UserConfig()
        if region is None:
            region = uc.region
        self._config = CosConfig(Secret_id=uc.secret_id, Secret_key=uc.secret_key,
                                 Region=region, Appid=uc.appid)
        self._client = CosS3Client(self._config)

    def upload_file2cos(self, bucket, file, key):
        # save funcs in the func directory
        try:
            response = self._client.put_object(Bucket=bucket,
                                               Body=file,
                                               Key=key,
                                               Metadata={
                                                   'x-cos-acl': 'public-read',
                                                   'Content-Type': 'application/x-zip-compressed',
                                               })
            if not response['ETag']:
                raise UploadToCosFailed("Upload func package failed")
        except Exception as e:
            error_msg = ""
            if "<?xml" in e.message:
                msg_dict = xmltodict.parse(e.message)
                if isinstance(msg_dict, dict):
                    error_msg_dict = msg_dict.get("Error", {})
                    error_msg = error_msg_dict.get("Code", "") + ", " + error_msg_dict.get("Message", "")
            else:
                error_msg = e.message
            raise UploadToCosFailed("Upload func package failed. {} ".format(error_msg))

        code_uri_in_cos = bucket + '/' + key
        return code_uri_in_cos
