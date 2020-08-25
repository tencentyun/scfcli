from .event import apigw_schema
from .event import cmq_schema
from .event import timer_schema
from .event import cos_schema
from .event import ckafka_schema
from .tcsam_macro import TcSamMacro as macro

func_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "tcsam.resource.ns.func", 
    "type": "object",
    "properties": {
        macro.Type: {"const": "TencentCloud::Serverless::Function"},
        macro.Properties: {
            "type": "object",
            "properties": {
                macro.CodeUri: {"type": ["string", "object"]},
                macro.Desc: {"type": "string"},
                macro.Role: {"type": "string"},
                macro.Envi: {
                    "type": "object",
                    "properties": {
                        macro.Vari: {
                            "type": ["object", "null"],
                            "properties": {},
                            "additionalProperties": {"type": "string"}
                        }
                    },
                    "required": [macro.Vari],
                    "additionalProperties": False
                },
                macro.Type: {"type": "string",
                             "enum": ["Event", "HTTP", "Service"]
                             },
                macro.Handler: {"type": "string"},
                macro.MemSize: {"type": "integer", "exclusiveMinimum": 0},
                macro.Runtime: {
                    "type": "string",
                    "enum": ["Python2.7", "Python3.6", "Nodejs6.10", "Nodejs8.9", "Nodejs10.15", "Nodejs12.16",
                    "Php5", "Php7", "Go1", "Java8", "python2.7", "python3.6", 
                    "nodejs6.10", "nodejs8.9", "nodejs10.15", "nodejs12.16", "php5", "php7", "go1", "java8"] #, "Nodejs8.9-service"]
                },
                macro.Timeout: {"type": "integer", "exclusiveMinimum": 0},
                macro.Events: {
                    "type": ["object", "null"],
                    "properties": {},
                    "additionalProperties": {
                        "type": "object",
                        "oneOf": [apigw_schema, cos_schema, timer_schema, cmq_schema, ckafka_schema]
                    }

                }, 
                macro.VpcConfig: {
                    "type": "object",
                    "properties":{
                        macro.VpcId: {"type": "string"},
                        macro.SubnetId: {"type": "string"}
                    },
                    "additionalProperties": False                  
                },
                macro.LocalZipFile: {"type": "string"}
            },
            "required": [macro.Handler, macro.Runtime, macro.CodeUri],
            "additionalProperties": False
        }
    },
    "required": [macro.Type, macro.Properties],
    "additionalProperties": False
}
