# -*- coding: utf-8 -*-

import time
import traceback
from threading import Thread
from six.moves.queue import Queue
from threading import Lock
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from tcfcli.common.user_config import UserConfig
from tcfcli.common.user_exceptions import UploadToCosFailed
from qcloud_cos.cos_comm import *
from tcfcli.common.operation_msg import Operation
from qcloud_cos.cos_auth import CosS3Auth
from qcloud_cos.version import __version__
from qcloud_cos.cos_threadpool import SimpleThreadPool


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
                Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
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

    def list_objects(self, Bucket, Prefix="", Delimiter="", Marker="", MaxKeys=1000, EncodingType="", **kwargs):
        """获取文件列表

        :param Bucket(string): 存储桶名称.
        :param Prefix(string): 设置匹配文件的前缀.
        :param Delimiter(string): 分隔符.
        :param Marker(string): 从marker开始列出条目.
        :param MaxKeys(int): 设置单次返回最大的数量,最大为1000.
        :param EncodingType(string): 设置返回结果编码方式,只能设置为url.
        :param kwargs(dict): 设置请求headers.
        :return(dict): 文件的相关信息，包括Etag等信息.

        .. code-block:: python

            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
            client = CosS3Client(config)
            # 列出bucket
            response = client.list_objects(
                Bucket='bucket',
                MaxKeys=100,
                Prefix='中文',
                Delimiter='/'
            )
        """
        decodeflag = True  # 是否需要对结果进行decode
        headers = mapped(kwargs)
        url = self._conf.uri(bucket=Bucket)

        params = {
            'prefix': Prefix,
            'delimiter': Delimiter,
            'marker': Marker,
            'max-keys': MaxKeys
        }
        if EncodingType:
            if EncodingType != 'url':
                raise CosClientError('EncodingType must be url')
            decodeflag = False  # 用户自己设置了EncodingType不需要去decode
            params['encoding-type'] = EncodingType
        else:
            params['encoding-type'] = 'url'
        params = format_values(params)
        rt = self.send_request(
            method='GET',
            url=url,
            bucket=Bucket,
            params=params,
            headers=headers,
            auth=CosS3Auth(self._conf, params=params))
        data = xml_to_dict(rt.content)
        format_dict(data, ['Contents', 'CommonPrefixes'])
        if decodeflag:
            decode_result(
                data,
                [
                    'Prefix',
                    'Marker',
                    'NextMarker'
                ],
                [
                    ['Contents', 'Key'],
                    ['CommonPrefixes', 'Prefix']
                ]
            )
        return data

    def copy_object(self, Bucket, Key, CopySource, CopyStatus='Copy', **kwargs):
        """文件拷贝，文件信息修改

        :param Bucket(string): 存储桶名称.
        :param Key(string): 上传COS路径.
        :param CopySource(dict): 拷贝源,包含Appid,Bucket,Region,Key.
        :param CopyStatus(string): 拷贝状态,可选值'Copy'|'Replaced'.
        :param kwargs(dict): 设置请求headers.
        :return(dict): 拷贝成功的结果.

        .. code-block:: python

            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
            client = CosS3Client(config)
            # 文件拷贝
            copy_source = {'Bucket': 'test04-1252448703', 'Key': '/test.txt', 'Region': 'ap-beijing-1'}
            response = client.copy_object(
                Bucket='bucket',
                Key='test.txt',
                CopySource=copy_source
            )
        """
        headers = mapped(kwargs)
        headers['x-cos-copy-source'] = gen_copy_source_url(CopySource)
        if CopyStatus != 'Copy' and CopyStatus != 'Replaced':
            raise CosClientError('CopyStatus must be Copy or Replaced')
        headers['x-cos-metadata-directive'] = CopyStatus
        url = self._conf.uri(bucket=Bucket, path=Key)
        rt = self.send_request(
            method='PUT',
            url=url,
            bucket=Bucket,
            auth=CosS3Auth(self._conf, Key),
            headers=headers)
        body = xml_to_dict(rt.content)
        if 'ETag' not in body:
            raise CosServiceError('PUT', rt.content, 200)
        data = dict(**rt.headers)
        data.update(body)
        return data

    def upload_file(self, Bucket, Key, LocalFilePath, PartSize=1, MAXThread=5, EnableMD5=False, **kwargs):
        """小于等于20MB的文件简单上传，大于20MB的文件使用分块上传

        :param Bucket(string): 存储桶名称.
        :param key(string): 分块上传路径名.
        :param LocalFilePath(string): 本地文件路径名.
        :param PartSize(int): 分块的大小设置,单位为MB.
        :param MAXThread(int): 并发上传的最大线程数.
        :param EnableMD5(bool): 是否打开MD5校验.
        :param kwargs(dict): 设置请求headers.
        :return(dict): 成功上传文件的元信息.

        .. code-block:: python

            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
            client = CosS3Client(config)
            # 根据文件大小自动选择分块大小,多线程并发上传提高上传速度
            file_name = 'thread_1GB_test'
            response = client.upload_file(
                Bucket='bucket',
                Key=file_name,
                LocalFilePath=file_name,
                PartSize=10,
                MAXThread=10,
            )
        """
        file_size = os.path.getsize(LocalFilePath)
        if file_size <= 1024 * 1024 * 20:
            with open(LocalFilePath, 'rb') as fp:
                rt = self.put_object(Bucket=Bucket, Key=Key, Body=fp, EnableMD5=EnableMD5, **kwargs)
            return rt
        else:
            part_size = 1024 * 1024 * PartSize  # 默认按照1MB分块,最大支持10G的文件，超过10G的分块数固定为10000
            last_size = 0  # 最后一块可以小于1MB
            parts_num = file_size // part_size
            last_size = file_size % part_size

            if last_size != 0:
                parts_num += 1
            else:  # 如果刚好整除,最后一块的大小等于分块大小
                last_size = part_size
            if parts_num > 10000:
                parts_num = 10000
                part_size = file_size // parts_num
                last_size = file_size % parts_num
                last_size += part_size

            # 创建分块上传
            # 判断是否可以断点续传
            resumable_flag = False
            already_exist_parts = {}
            uploadid = self._get_resumable_uploadid(Bucket, Key)
            if uploadid is not None:
                # 校验服务端返回的每个块的信息是否和本地的每个块的信息相同,只有校验通过的情况下才可以进行断点续传
                resumable_flag = self._check_all_upload_parts(Bucket, Key, uploadid, LocalFilePath, parts_num,
                                                              part_size, last_size, already_exist_parts)
            # 如果不能断点续传,则创建一个新的分块上传
            if not resumable_flag:
                rt = self.create_multipart_upload(Bucket=Bucket, Key=Key, **kwargs)
                uploadid = rt['UploadId']

            # 上传分块
            offset = 0  # 记录文件偏移量
            lst = list()  # 记录分块信息
            pool = SimpleThreadPool(MAXThread)

            for i in range(1, parts_num + 1):
                if i == parts_num:  # 最后一块
                    pool.add_task(self._upload_part, Bucket, Key, LocalFilePath, offset, file_size - offset, i,
                                  uploadid, lst, resumable_flag, already_exist_parts, EnableMD5)
                else:
                    pool.add_task(self._upload_part, Bucket, Key, LocalFilePath, offset, part_size, i, uploadid, lst,
                                  resumable_flag, already_exist_parts, EnableMD5)
                    offset += part_size
            pool.wait_completion()
            result = pool.get_result()
            if not result['success_all'] or len(lst) != parts_num:
                raise CosClientError('some upload_part fail after max_retry, please upload_file again')
            lst = sorted(lst, key=lambda x: x['PartNumber'])  # 按PartNumber升序排列
            # 完成分块上传
            rt = self.complete_multipart_upload(Bucket=Bucket, Key=Key, UploadId=uploadid,
                                                MultipartUpload={'Part': lst})
            return rt

    def complete_multipart_upload(self, Bucket, Key, UploadId, MultipartUpload={}, **kwargs):
        """完成分片上传,除最后一块分块块大小必须大于等于1MB,否则会返回错误.

        :param Bucket(string): 存储桶名称.
        :param Key(string): COS路径.
        :param UploadId(string): 分块上传创建的UploadId.
        :param MultipartUpload(dict): 所有分块的信息,包含Etag和PartNumber.
        :param kwargs(dict): 设置请求headers.
        :return(dict): 上传成功返回的结果，包含整个文件的ETag等信息.

        .. code-block:: python

            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
            client = CosS3Client(config)
            # 分块上传
            response = client.complete_multipart_upload(
                Bucket='bucket',
                Key='multipartfile.txt',
                UploadId='uploadid',
                MultipartUpload={'Part': lst}
            )
        """
        headers = mapped(kwargs)
        params = {'uploadId': UploadId}
        params = format_values(params)
        url = self._conf.uri(bucket=Bucket, path=Key)
        rt = self.send_request(
            method='POST',
            url=url,
            bucket=Bucket,
            auth=CosS3Auth(self._conf, Key, params=params),
            data=dict_to_xml(MultipartUpload),
            timeout=1200,  # 分片上传大文件的时间比较长，设置为20min
            headers=headers,
            params=params)
        body = xml_to_dict(rt.content)
        # 分块上传文件返回200OK并不能代表文件上传成功,返回的body里面如果没有ETag则认为上传失败
        if 'ETag' not in body:
            raise CosServiceError('POST', rt.content, 200)
        data = dict(**rt.headers)
        data.update(body)
        return data

    # Advanced interface
    def _upload_part(self, bucket, key, local_path, offset, size, part_num, uploadid, md5_lst, resumable_flag,
                     already_exist_parts, enable_md5):
        """从本地文件中读取分块, 上传单个分块,将结果记录在md5——list中

        :param bucket(string): 存储桶名称.
        :param key(string): 分块上传路径名.
        :param local_path(string): 本地文件路径名.
        :param offset(int): 读取本地文件的分块偏移量.
        :param size(int): 读取本地文件的分块大小.
        :param part_num(int): 上传分块的序号.
        :param uploadid(string): 分块上传的uploadid.
        :param md5_lst(list): 保存上传成功分块的MD5和序号.
        :param resumable_flag(bool): 是否为断点续传.
        :param already_exist_parts(dict): 断点续传情况下,保存已经上传的块的序号和Etag.
        :param enable_md5(bool): 是否开启md5校验.
        :return: None.
        """
        # 如果是断点续传且该分块已经上传了则不用实际上传
        if resumable_flag and part_num in already_exist_parts:
            md5_lst.append({'PartNumber': part_num, 'ETag': already_exist_parts[part_num]})
        else:
            with open(local_path, 'rb') as fp:
                fp.seek(offset, 0)
                data = fp.read(size)
            rt = self.upload_part(bucket, key, data, part_num, uploadid, enable_md5)
            md5_lst.append({'PartNumber': part_num, 'ETag': rt['ETag']})
        return None

    def upload_part(self, Bucket, Key, Body, PartNumber, UploadId, EnableMD5=False, **kwargs):
        """上传分块，单个大小不得超过5GB

        :param Bucket(string): 存储桶名称.
        :param Key(string): COS路径.
        :param Body(file|string): 上传分块的内容,可以为文件流或者字节流.
        :param PartNumber(int): 上传分块的编号.
        :param UploadId(string): 分块上传创建的UploadId.
        :param kwargs(dict): 设置请求headers.
        :param EnableMD5(bool): 是否需要SDK计算Content-MD5，打开此开关会增加上传耗时.
        :return(dict): 上传成功返回的结果，包含单个分块ETag等信息.

        .. code-block:: python

            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
            client = CosS3Client(config)
            # 分块上传
            with open('test.txt', 'rb') as fp:
                data = fp.read(1024*1024)
                response = client.upload_part(
                    Bucket='bucket',
                    Body=data,
                    Key='test.txt'
                )
        """
        check_object_content_length(Body)
        headers = mapped(kwargs)
        params = {'partNumber': PartNumber, 'uploadId': UploadId}
        params = format_values(params)
        url = self._conf.uri(bucket=Bucket, path=Key)
        if EnableMD5:
            md5_str = get_content_md5(Body)
            if md5_str:
                headers['Content-MD5'] = md5_str
        rt = self.send_request(
            method='PUT',
            url=url,
            bucket=Bucket,
            headers=headers,
            params=params,
            auth=CosS3Auth(self._conf, Key, params=params),
            data=Body)
        response = dict()
        response['ETag'] = rt.headers['ETag']
        return response

    def list_multipart_uploads(self, Bucket, Prefix="", Delimiter="", KeyMarker="", UploadIdMarker="", MaxUploads=1000,
                               EncodingType="", **kwargs):
        """获取Bucket中正在进行的分块上传

        :param Bucket(string): 存储桶名称.
        :param Prefix(string): 设置匹配文件的前缀.
        :param Delimiter(string): 分隔符.
        :param KeyMarker(string): 从KeyMarker指定的Key开始列出条目.
        :param UploadIdMarker(string): 从UploadIdMarker指定的UploadID开始列出条目.
        :param MaxUploads(int): 设置单次返回最大的数量,最大为1000.
        :param EncodingType(string): 设置返回结果编码方式,只能设置为url.
        :param kwargs(dict): 设置请求headers.
        :return(dict): 文件的相关信息，包括Etag等信息.

        .. code-block:: python

            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
            client = CosS3Client(config)
            # 列出所有分块上传
            response = client.list_multipart_uploads(
                Bucket='bucket',
                MaxUploads=100,
                Prefix='中文',
                Delimiter='/'
            )
        """
        headers = mapped(kwargs)
        decodeflag = True
        url = self._conf.uri(bucket=Bucket)
        params = {
            'uploads': '',
            'prefix': Prefix,
            'delimiter': Delimiter,
            'key-marker': KeyMarker,
            'upload-id-marker': UploadIdMarker,
            'max-uploads': MaxUploads
        }
        if EncodingType:
            if EncodingType != 'url':
                raise CosClientError('EncodingType must be url')
            decodeflag = False
            params['encoding-type'] = EncodingType
        else:
            params['encoding-type'] = 'url'
        params = format_values(params)
        rt = self.send_request(
            method='GET',
            url=url,
            bucket=Bucket,
            params=params,
            headers=headers,
            auth=CosS3Auth(self._conf, params=params))

        data = xml_to_dict(rt.content)
        format_dict(data, ['Upload', 'CommonPrefixes'])
        if decodeflag:
            decode_result(
                data,
                [
                    'Prefix',
                    'KeyMarker',
                    'NextKeyMarker',
                    'UploadIdMarker',
                    'NextUploadIdMarker'
                ],
                [
                    ['Upload', 'Key'],
                    ['CommonPrefixes', 'Prefix']
                ]
            )
        return data

    def create_multipart_upload(self, Bucket, Key, **kwargs):
        """创建分块上传，适用于大文件上传

        :param Bucket(string): 存储桶名称.
        :param Key(string): COS路径.
        :param kwargs(dict): 设置请求headers.
        :return(dict): 初始化分块上传返回的结果，包含UploadId等信息.

        .. code-block:: python

            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
            client = CosS3Client(config)
            # 创建分块上传
            response = client.create_multipart_upload(
                Bucket='bucket',
                Key='test.txt'
            )
        """
        headers = mapped(kwargs)
        params = {'uploads': ''}
        params = format_values(params)
        url = self._conf.uri(bucket=Bucket, path=Key)
        rt = self.send_request(
            method='POST',
            url=url,
            bucket=Bucket,
            auth=CosS3Auth(self._conf, Key, params=params),
            headers=headers,
            params=params)

        data = xml_to_dict(rt.content)
        return data


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
                # Operation(str(response)).warning()
                raise UploadToCosFailed("Upload func package failed [No ETag].")
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
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
                raise UploadToCosFailed(str(e))

        code_uri_in_cos = bucket + '/' + key
        return code_uri_in_cos

    def upload_file2cos2(self, bucket, file, key, max_thread=5):
        try:
            response = self._client.upload_file(Bucket=bucket,
                                                LocalFilePath=file,
                                                Key=key,
                                                MAXThread=max_thread,
                                                # EnableMD5=md5,
                                                Metadata={
                                                    'x-cos-acl': 'public-read',
                                                    'Content-Type': 'application/x-zip-compressed',
                                                })
            if not response['ETag']:
                return "Upload func package failed [No ETag]."
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            try:
                if "<?xml" in str(e):
                    error_code = re.findall("<Code>(.*?)</Code>", str(e))[0]
                    error_message = re.findall("<Message>(.*?)</Message>", str(e))[0]
                    return "COS client error code: %s, message: %s" % (error_code, error_message)
                else:
                    return str(e)
            finally:
                # raise UploadToCosFailed("Upload func package failed.")
                return str(e)

        return True

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
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return (-1, e)

    def get_bucket(self, bucket):
        '''
            通过get_bucket_list()方法，获得bucket list，再根据地域和bucket筛选目标bucket。
            这里可以考虑使用head_bucket(Bucket)，但是目前这个方法异常：qcloud_cos.cos_exception.CosServiceError / 2019-07-28
            后期这个方法恢复，可以作为一个优化点，对该部分进行优化。
        :param bucket: str  bucket名称
        :return: 1表示找到了指定Region的Bucket，0表示没找到，error表示错误
        '''
        try:
            temp_data = self.get_bucket_list()
            # print(temp_data)
            if temp_data[0] == 0:
                bucket_list = temp_data[1]
                for eve_bucket in bucket_list:
                    if eve_bucket["Location"] == self._region and eve_bucket["Name"] == bucket:
                        return 1
                return 0
            else:
                error = temp_data[1]
                return error
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
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
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return e

    def get_object_list(self, bucket, prefix):
        try:
            response = self._client.list_objects(
                Bucket=bucket,
                Prefix=prefix,
                Delimiter='/',
            )
            return response
        except Exception as e:
            Operation(e, err_msg=traceback.format_exc(), level="ERROR").no_output()
            return e

    def copy_object(self, bucket_name, old_key, new_key):
        try:
            response = self._client.copy_object(
                Bucket=bucket_name,
                Key=new_key,
                CopySource={
                    'Bucket': bucket_name,
                    'Key': old_key,
                    'Region': self._region
                },
                CopyStatus='Copy'
            )
            return response
        except Exception as e:
            return e


class SimpleThreadPool:

    def __init__(self, num_threads=5, num_queue=0):
        self._num_threads = num_threads
        self._queue = Queue(num_queue)
        self._lock = Lock()
        self._active = False
        self._workers = list()
        self._finished = False

    def add_task(self, func, *args, **kwargs):
        if not self._active:
            with self._lock:
                if not self._active:
                    self._workers = []
                    self._active = True

                    for i in range(self._num_threads):
                        w = WorkerThread(self._queue)
                        self._workers.append(w)
                        w.start()

        self._queue.put((func, args, kwargs))

    def wait_completion(self):
        self._queue.join()
        self._finished = True
        # 已经结束的任务, 需要将线程都退出, 防止卡死
        for i in range(self._num_threads):
            self._queue.put((None, None, None))

        self._active = False

    def get_result(self):
        assert self._finished
        detail = [worker.get_result() for worker in self._workers]
        succ_all = all([tp[1] == 0 for tp in detail])
        return {'success_all': succ_all, 'detail': detail}


class WorkerThread(Thread):
    def __init__(self, task_queue, *args, **kwargs):
        super(WorkerThread, self).__init__(*args, **kwargs)

        self._task_queue = task_queue
        self._succ_task_num = 0
        self._fail_task_num = 0
        self._ret = list()

    def run(self):
        while True:
            func, args, kwargs = self._task_queue.get()
            # 判断线程是否需要退出
            if func is None:
                return
            try:
                ret = func(*args, **kwargs)
                self._succ_task_num += 1
                self._ret.append(ret)

            except Exception as e:
                self._fail_task_num += 1
                self._ret.append(e)
            finally:
                self._task_queue.task_done()

    def get_result(self):
        return self._succ_task_num, self._fail_task_num, self._ret
