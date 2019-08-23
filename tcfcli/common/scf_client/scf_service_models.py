# -*- coding: utf8 -*-
# Copyright (c) 2017-2018 THL A29 Limited, a Tencent company. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tencentcloud.common.abstract_model import AbstractModel


class Code(AbstractModel):
    def __init__(self):
        self.CosBucketName = None
        self.CosObjectName = None
        self.CosBucketRegion = None

    def _deserialize(self, params):
        self.CosBucketName = params.get("CosBucketName")
        self.CosObjectName = params.get("CosObjectName")
        self.CosBucketRegion = params.get("CosBucketRegion")


class CreateFunctionRequest(AbstractModel):
    def __init__(self):
        self.FunctionName = None
        self.Code = None
        self.Handler = None
        self.Description = None
        self.MemorySize = None
        self.Environment = None
        self.Runtime = None
        self.VpcConfig = None
        self.Type = None

    def _deserialize(self, params):
        self.FunctionName = params.get("FunctionName")
        if params.get("Code") is not None:
            self.Code = Code()
            self.Code._deserialize(params.get("Code"))
        self.Handler = params.get("Handler")
        self.Description = params.get("Description")
        self.MemorySize = params.get("MemorySize")
        if params.get("Environment") is not None:
            self.Environment = Environment()
            self.Environment._deserialize(params.get("Environment"))
        self.Runtime = params.get("Runtime")
        if params.get("VpcConfig") is not None:
            self.VpcConfig = VpcConfig()
            self.VpcConfig._deserialize(params.get("VpcConfig"))
        self.Type = params.get("Type")


class CreateFunctionResponse(AbstractModel):
    def __init__(self):
        self.RequestId = None

    def _deserialize(self, params):
        self.RequestId = params.get("RequestId")


class DeleteFunctionRequest(AbstractModel):

    def __init__(self):
        self.FunctionName = None

    def _deserialize(self, params):
        self.FunctionName = params.get("FunctionName")


class DeleteFunctionResponse(AbstractModel):

    def __init__(self):

        self.RequestId = None

    def _deserialize(self, params):
        self.RequestId = params.get("RequestId")


class Environment(AbstractModel):

    def __init__(self):

        self.Variables = None

    def _deserialize(self, params):
        if params.get("Variables") is not None:
            self.Variables = []
            for item in params.get("Variables"):
                obj = Variable()
                obj._deserialize(item)
                self.Variables.append(obj)


class Function(AbstractModel):
    def __init__(self):
        self.ModTime = None
        self.AddTime = None
        self.Runtime = None
        self.FunctionName = None
        self.FunctionId = None
        self.Namespace = None
        self.Status = None
        self.StatusDesc = None
        self.Description = None

    def _deserialize(self, params):
        self.ModTime = params.get("ModTime")
        self.AddTime = params.get("AddTime")
        self.Runtime = params.get("Runtime")
        self.FunctionName = params.get("FunctionName")
        self.FunctionId = params.get("FunctionId")
        self.Namespace = params.get("Namespace")
        self.Status = params.get("Status")
        self.StatusDesc = params.get("StatusDesc")
        self.Description = params.get("Description")


class UpdateFunctionCodeRequest(AbstractModel):
    def __init__(self):
        self.Handler = None
        self.FunctionName = None
        self.CosBucketName = None
        self.CosObjectName = None
        self.CosBucketRegion = None

    def _deserialize(self, params):
        self.Handler = params.get("Handler")
        self.FunctionName = params.get("FunctionName")
        self.CosBucketName = params.get("CosBucketName")
        self.CosObjectName = params.get("CosObjectName")
        self.CosBucketRegion = params.get("CosBucketRegion")


class UpdateFunctionCodeResponse(AbstractModel):
    def __init__(self):
        self.RequestId = None

    def _deserialize(self, params):
        self.RequestId = params.get("RequestId")


class UpdateFunctionConfigurationRequest(AbstractModel):
    def __init__(self):

        self.FunctionName = None
        self.Description = None
        self.MemorySize = None
        self.Environment = None
        self.VpcConfig = None

    def _deserialize(self, params):
        self.FunctionName = params.get("FunctionName")
        self.Description = params.get("Description")
        self.MemorySize = params.get("MemorySize")
        if params.get("Environment") is not None:
            self.Environment = Environment()
            self.Environment._deserialize(params.get("Environment"))
        if params.get("VpcConfig") is not None:
            self.VpcConfig = VpcConfig()
            self.VpcConfig._deserialize(params.get("VpcConfig"))


class UpdateFunctionConfigurationResponse(AbstractModel):

    def __init__(self):
        self.RequestId = None

    def _deserialize(self, params):
        self.RequestId = params.get("RequestId")


class Variable(AbstractModel):

    def __init__(self):

        self.Key = None
        self.Value = None

    def _deserialize(self, params):
        self.Key = params.get("Key")
        self.Value = params.get("Value")


class VpcConfig(AbstractModel):

    def __init__(self):
        self.VpcId = None
        self.SubnetId = None

    def _deserialize(self, params):
        self.VpcId = params.get("VpcId")
        self.SubnetId = params.get("SubnetId")
