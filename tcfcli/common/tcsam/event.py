from .tcsam_macro import TcSamMacro as macro
from .tcsam_macro import TriggerMacro as trmacro
apigw_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "tcsam.ns.func.event.apigw",
    "type": "object",
    "properties": {
        macro.Type: {"const": macro.TrApiGw},
        macro.Properties: {
            "type": "object",
            "properties": {
                trmacro.StageName: {
                    "type": "string",
                    "enum": ["test", "prepub", "release"]
                },
                trmacro.HttpMethod: {
                    "type": "string",
                    "enum": ["ANY", "GET", "POST", "PUT", "DELETE", "HEAD"]
                },
                trmacro.IntegratedResp: {
                    "type": "boolean",
                },
                trmacro.Enable: {
                    "enum": ["OPEN", "CLOSE", True, False]
                }
            }
        }
    },
    "required": [macro.Type, macro.Properties],
    "additionalProperties": False
}



timer_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "tcsam.ns.func.event.timer",
    "type": "object",
    "properties": {
        macro.Type: {"const": macro.TrTimer},
        macro.Properties: {
            "type": "object",
            "properties": {
                trmacro.CronExp: {"type": "string"},
                trmacro.Enable: {
                    "enum": ["OPEN", "CLOSE", True, False]
                },
                trmacro.Message: {
                    "type": "string"
                }
            },
            "required": [trmacro.CronExp],
        },
    },
    "required": [macro.Type, macro.Properties],
    "additionalProperties": False,
}


cmq_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "tcsam.ns.func.event.cmq",
    "type": "object",
    "properties": {
        macro.Type: {"const": macro.TrCMQ},
        macro.Properties: {
            "type": ["object", "null"],
            "properties": {
                "Name": {"type": "string"},
                trmacro.Enable: {
                    "enum": ["OPEN", "CLOSE", True, False]
                }
            }
        }
    },
    "required": [macro.Type, macro.Properties],
    "additionalProperties": False
}


cos_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "tcsam.ns.func.event.cos",
    "type": "object",
    "properties": {
        macro.Type: {"const": macro.TrCOS},
        macro.Properties: {
            "type": "object",
            "properties": {
                trmacro.Filter: {
                    "type": "object",
                    "properties": {
                        trmacro.Prefix: {"type": "string"},
                        trmacro.Suffix: {"type": "string"}
                    }
                },
                trmacro.Bucket: {"type": "string"},
                macro.Events: {"type": "string"},
                trmacro.Enable: {
                    "enum": ["OPEN", "CLOSE", True, False]
                }
            },
            "required": [macro.Events]
        }
    },
    "required": [macro.Type, macro.Properties],
    "additionalProperties": False
}


ckafka_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "tcsam.ns.func.event.ckafka",
    "type": "object",
    "properties": {
        macro.Type: {"const": macro.TrCKafka},
        macro.Properties: {
            "type": "object",
            "properties": {
                trmacro.Name: {"type": "string"},
                trmacro.Topic: {"type": "string"},
                trmacro.MaxMsgNum: {"type": "integer"},
                trmacro.Offset: {"type": "string"},
                trmacro.Enable: {
                    "enum": ["OPEN", "CLOSE", True, False]
                }
            },
            "required": [trmacro.Name, trmacro.Topic, trmacro.MaxMsgNum]
        }
    },
    "required": [macro.Type, macro.Properties],
    "additionalProperties": False
}