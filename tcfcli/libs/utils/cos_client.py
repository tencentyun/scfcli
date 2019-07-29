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
        self._region = region
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
            # error_msg = ""
            # if "<?xml" in e.message:
            #     msg_dict = xmltodict.parse(e.message)
            #     if isinstance(msg_dict, dict):
            #         error_msg_dict = msg_dict.get("Error", {})
            #         error_msg = error_msg_dict.get("Code", "") + ", " + error_msg_dict.get("Message", "")
            # else:
            #     error_msg = e.message
            # raise UploadToCosFailed("Upload func package failed. {} ".format(error_msg))
            raise UploadToCosFailed("Upload func package failed.")

        code_uri_in_cos = bucket + '/' + key
        return code_uri_in_cos

    def get_bucket_list(self):
        '''
            获取bucket列表
        :return: tuple(状态，信息)，如果是成功获得到了bucket list，状态为0，信息为list，否则状态为-1，信息为error
        '''
        try:
            response = self._client.list_buckets()
            bucket_list = response['Buckets']['Bucket']
            return (0, bucket_list)
        except Exception as e:
            return (-1, e)

    def get_bucket(self, bucket):
        '''
            通过get_bucket_list()方法，获得bucket list，再根据地域和bucket筛选目标bucket。
            这里可以考虑使用head_bucket(Bucket)，但是目前这个方法异常：qcloud_cos.cos_exception.CosServiceError / 2019-07-28
            后期这个方法恢复，可以作为一个优化点，对该部分进行优化。
        :param bucket: str  bucket名称
        :return: 0表示找到了指定Region的Bucket，-1表示没找到，error表示错误
        '''
        try:
            temp_data = self.get_bucket_list()
            if temp_data[0] == 0:
                bucket_list = temp_data[1]
                for eve_bucket in bucket_list:
                    if eve_bucket["Location"] == self._region and eve_bucket["Name"] == bucket:
                        return 0
                return -1
            else:
                error = temp_data[1]
                return error
        except Exception as e:
            return e

    def creat_bucket(self, bucket):
        '''
            根据bucket和config里面的region进行Bucket创建
        :param bucket: str  bucket名字
        :return: True表示创建成功，error表示错误
        '''
        try:
            self._client.create_bucket(
                Bucket=bucket,
                ACL='private',
            )
            return True
        except Exception as e:
            return e
