import xmltodict
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from tcfcli.common.user_config import UserConfig
from tcfcli.common.user_exceptions import UploadToCosFailed
from qcloud_cos.cos_comm import *
from tcfcli.common.operation_msg import Operation
from qcloud_cos.cos_auth import CosS3Auth
from qcloud_cos.version import __version__


class CosReset(CosS3Client):

    def send_request(self, method, url, bucket, timeout=30, **kwargs):
        """封装request库发起http请求"""
        if self._conf._timeout is not None:  # 用户自定义超时时间
            timeout = self._conf._timeout
        if self._conf._ua is not None:
            kwargs['headers']['User-Agent'] = self._conf._ua
        else:
            kwargs['headers']['User-Agent'] = 'cos-python-sdk-v' + __version__
        if self._conf._token is not None:
            kwargs['headers']['x-cos-security-token'] = self._conf._token
        if bucket is not None:
            kwargs['headers']['Host'] = self._conf.get_host(bucket)
        kwargs['headers'] = format_values(kwargs['headers'])
        if 'data' in kwargs:
            kwargs['data'] = to_bytes(kwargs['data'])
        for j in range(self._retry + 1):
            try:
                if method == 'POST':
                    res = self._session.post(url, timeout=timeout, **kwargs)
                elif method == 'GET':
                    res = self._session.get(url, timeout=timeout, **kwargs)
                elif method == 'PUT':
                    res = self._session.put(url, timeout=timeout, **kwargs)
                elif method == 'DELETE':
                    res = self._session.delete(url, timeout=timeout, **kwargs)
                elif method == 'HEAD':
                    res = self._session.head(url, timeout=timeout, **kwargs)
                if res.status_code < 400:  # 2xx和3xx都认为是成功的
                    return res
            except Exception as e:  # 捕获requests抛出的如timeout等客户端错误,转化为客户端错误
                if j < self._retry:
                    continue
                raise CosClientError(str(e))

        if res.status_code >= 400:  # 所有的4XX,5XX都认为是COSServiceError
            if method == 'HEAD' and res.status_code == 404:  # Head 需要处理
                info = dict()
                info['code'] = 'NoSuchResource'
                info['message'] = 'The Resource You Head Not Exist'
                info['resource'] = url
                if 'x-cos-request-id' in res.headers:
                    info['requestid'] = res.headers['x-cos-request-id']
                if 'x-cos-trace-id' in res.headers:
                    info['traceid'] = res.headers['x-cos-trace-id']
                raise CosServiceError(method, info, res.status_code)
            else:
                msg = res.text
                if msg == u'':  # 服务器没有返回Error Body时 给出头部的信息
                    msg = res.headers
                raise CosServiceError(method, msg, res.status_code)

        return None

    #  s3 object interface begin
    def put_object(self, Bucket, Body, Key, EnableMD5=False, **kwargs):
        """单文件上传接口，适用于小文件，最大不得超过5GB

        :param Bucket(string): 存储桶名称.
        :param Body(file|string): 上传的文件内容，类型为文件流或字节流.
        :param Key(string): COS路径.
        :param EnableMD5(bool): 是否需要SDK计算Content-MD5，打开此开关会增加上传耗时.
        :kwargs(dict): 设置上传的headers.
        :return(dict): 上传成功返回的结果，包含ETag等信息.

        .. code-block:: python

            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
            client = CosS3Client(config)
            # 上传本地文件到cos
            with open('test.txt', 'rb') as fp:
                response = client.put_object(
                    Bucket='bucket',
                    Body=fp,
                    Key='test.txt'
                )
                print (response['ETag'])
        """
        check_object_content_length(Body)
        headers = mapped(kwargs)
        url = self._conf.uri(bucket=Bucket, path=Key)
        if EnableMD5:
            md5_str = get_content_md5(Body)
            if md5_str:
                headers['Content-MD5'] = md5_str
        rt = self.send_request(
            method='PUT',
            url=url,
            bucket=Bucket,
            auth=CosS3Auth(self._conf, Key),
            data=Body,
            headers=headers)

        response = dict(**rt.headers)
        return response

    # s3 bucket interface begin
    def create_bucket(self, Bucket, **kwargs):
        """创建一个bucket

        :param Bucket(string): 存储桶名称.
        :param kwargs(dict): 设置请求headers.
        :return: None.

        .. code-block:: python

            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
            client = CosS3Client(config)
            # 创建bucket
            response = client.create_bucket(
                Bucket='bucket'
            )
        """
        headers = mapped(kwargs)
        url = self._conf.uri(bucket=Bucket)
        rt = self.send_request(
            method='PUT',
            url=url,
            bucket=Bucket,
            auth=CosS3Auth(self._conf),
            headers=headers)
        return None


class CosClient(object):

    def __init__(self, region=None):
        uc = UserConfig()
        if region is None:
            region = uc.region
        self._region = region
        self._config = CosConfig(Secret_id=uc.secret_id, Secret_key=uc.secret_key,
                                 Region=region, Appid=uc.appid)
        self._client = CosReset(self._config)

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
            try:
                if "<?xml" in str(e):
                    error_code = re.findall("<Code>(.*?)</Code>", str(e))[0]
                    error_message = re.findall("<Message>(.*?)</Message>", str(e))[0]
                    Operation("COS client error code: %s, message: %s" % (error_code, error_message)).warning()
            finally:
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

    def create_bucket(self, bucket):
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
