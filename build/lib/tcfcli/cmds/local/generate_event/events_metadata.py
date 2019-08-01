# -*- coding: utf-8 -*-

from tcfcli.help.message import CommonHelp as help

EVENTS_METADATA = {
    "cmq": {
        "notification": {
            "filename": "notify",
            "help": help.EVENTS_CMQ_NOTIFICATION,
            "params": {
                "owner": {
                    "default": 12345678,
                }
            }
        }
    },
    "ckafka": {
        "consume": {
            "filename": "consume",
            "help": help.EVENTS_CKAFKA_CONSUME,
            "params": {
            }
        }
    },
    "apigateway": {
        "proxy": {
            "filename": "proxy",
            "help": help.EVENTS_APIGATEWAY_PROXY,
            "params": {
                "body": {
                    "default": "{\"msg\": \"hello apigateway\"}",
                }
            }
        }
    },
    "timer": {
        "timeup": {
            "filename": "timeout",
            "help": help.EVENTS_TIMER_TIMEUP,
            "params": {
                "message": {
                    "default": "hello timer",
                }
            }
        }
    },
    "cos": {
        "put": {
            "filename": "put",
            "help": help.EVENTS_COS_PUT,
            "params": {
            }
        },
        "post": {
            "filename": "post",
            "help": help.EVENTS_COS_POST,
            "params": {
            }
        },
        "delete": {
            "filename": "delete",
            "help": help.EVENTS_COS_DELETE,
            "params": {
            }
        }
    }
}

EVENTS_HELP = {
    "cmq": help.EVENTS_CMQ,
    "cos": help.EVENTS_COS,
    "timer": help.EVENTS_TIMER,
    "apigateway": help.EVENTS_APIGATEWAY,
    "ckafka": help.EVENTS_CKAFKA,
}
