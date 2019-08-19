# -*- coding: utf-8 -*-

import os
import platform
from tcfcli.common.operation_msg import Operation


home = os.path.expanduser('~')
_USER_CONFIG_FILE = home + '/.tcli_config.ini'

version = platform.python_version()
if version >= '3':
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser


class CliConfigParser(ConfigParser):

    def __init__(self, defaults=None):
        ConfigParser.__init__(self, defaults=None)
        # super(CliConfigParser, self).__init__(defaults)

    def optionxform(self, optionstr):
        return optionstr


class UserConfig(object):
    API = "API"
    USER_QCLOUD_CONFIG = "USER_QCLOUD_CONFIG"
    GIT_CONFIG = "GIT_CONFIG"
    ENV = "ENV"
    OTHERS = "OTHERS"
    SECTION_LIST = [USER_QCLOUD_CONFIG, GIT_CONFIG, ENV, OTHERS]
    COMMON_SECTION_LIST = [GIT_CONFIG, ENV, OTHERS]

    def __init__(self):
        self.secret_id = "None"
        self.secret_key = "None"
        self.region = "None"
        self.appid = "None"
        self.using_cos = "False (By default, it isn't deployed by COS.)"
        self.python2_path = "None"
        self.python3_path = "None"
        self.version_time = ""

        self.section_map = {
            UserConfig.USER_QCLOUD_CONFIG: {
                "secret_id": "None",
                "secret_key": "None",
                "region": "None",
                "appid": "None",
                "using_cos": "False (By default, it isn't deployed by COS.)"
             },
            UserConfig.GIT_CONFIG: {
                "git_url": "None",
                "git_username": "None",
                "git_password": "None"
            },
            UserConfig.ENV: {
                "python2_path": "None",
                "python3_path": "None",
            },
           UserConfig.OTHERS: {
               "curr_user": "None",
               "version_time": "",
               "no_color": "None",
               "language": "None",
               "allow_report": "None",
           }
        }
        self._migrate()
        self._load_config()
        self._dumpattr()

    def _migrate(self):#新老配置迁移函数
        cf = CliConfigParser()
        if not cf.read(_USER_CONFIG_FILE):
            return
        if UserConfig.API not in cf.sections():#无旧有API标志,不迁移
            return
        for section in cf.sections():#若有新版本用户标志section,不迁移
            if section.startswith('USER_'):
                return
        #读取旧的section数据
        attrs = {}
        for attrs_keys in cf.options(UserConfig.API):
            attrs[attrs_keys] = cf.get(UserConfig.API, attrs_keys)
        self.set_attrs(attrs)
        self.section_map[UserConfig.OTHERS]['curr_user'] = 'USER_'+str(1)
        self._dump_config()

    def _dumpattr(self):
        for section in self.section_map:
            if section not in UserConfig.SECTION_LIST:
                break
            for key in list(self.section_map[section].keys()):
                if key in vars(self):
                    setattr(self, key, self.section_map[section][key])

    def set_attrs(self, attrs):
        for attr_key in attrs:
            for section in self.section_map:
                if section not in UserConfig.SECTION_LIST: #避免设置其他用户的属性
                    continue
                if self._name_attr2obj(attr_key) in list(self.section_map[section].keys()):
                    self.section_map[section][self._name_attr2obj(attr_key)] = attrs[attr_key]

    def get_attrs(self, attrs):
        ret = {}
        for attr_key in [k for k, v in attrs.items() if v]:
            for section in self.section_map:
                if section not in UserConfig.SECTION_LIST:
                    continue
                if self._name_attr2obj(attr_key) in self.section_map[section].keys():
                    ret[self._name_obj2attr(attr_key)] = self.section_map[section][self._name_attr2obj(attr_key)]
        return ret

    def flush(self):
        self._dump_config()

    def _get_curr_user_section(self):
        cf = CliConfigParser()
        if not cf.read(_USER_CONFIG_FILE):
            return None
        if UserConfig.OTHERS not in cf.sections():
            return None
        return cf.get(UserConfig.OTHERS, self._name_obj2attr('curr_user'))

    def get_all_user(self):
        cf = CliConfigParser()
        userlist=[]
        if not cf.read(_USER_CONFIG_FILE):
            return None
        for section in cf.sections():  # 若有新版本用户标志section,不迁移
            if section.startswith('USER_'):
                userlist.append(section)
        return userlist

    def add_user(self, data):
        userlist = self.get_all_user()
        user_section = 'USER_'
        for i in range(100):
            user_section = 'USER_'+str(i+1)
            if user_section not in userlist:
                break

        self.section_map[user_section] = {}
        for key in list(self.section_map[UserConfig.USER_QCLOUD_CONFIG].keys()):
            self.section_map[user_section][key] = data[self._name_obj2attr(key)]

    def changeuser(self, user):
        self.section_map[UserConfig.OTHERS]['curr_user'] = user
        for key in list(self.section_map[UserConfig.USER_QCLOUD_CONFIG].keys()):
            self.section_map[UserConfig.USER_QCLOUD_CONFIG][key] = self.section_map[user][key]

    def get_user_appid(self, user):
        return self.section_map[user]['appid']

    def _load_config(self):
        cf = CliConfigParser()
        if not cf.read(_USER_CONFIG_FILE):
            return
        #获取当前用户
        curr_user = self._get_curr_user_section()
        if not curr_user:
            return

        for section in cf.sections():
            if section not in UserConfig.SECTION_LIST and not section.startswith('USER_'):
                continue
            attrs = cf.options(section)

            # 获取当前用户配置到对象
            if section == curr_user:
                for attr in attrs:
                    if self._name_attr2obj(attr) in list(self.section_map[UserConfig.USER_QCLOUD_CONFIG].keys()):
                        self.section_map[UserConfig.USER_QCLOUD_CONFIG][self._name_attr2obj(attr)] = cf.get(section, attr)
            # 获取所有用户配置到对象，包括当前用户
            if section.startswith('USER_'):
                self.section_map[section] = {}
                for attr in attrs:
                    if self._name_attr2obj(attr) in list(self.section_map[UserConfig.USER_QCLOUD_CONFIG].keys()):
                        self.section_map[section][self._name_attr2obj(attr)] = cf.get(section, attr)
            # 获取共有配置到对象
            else:
                for attr in attrs:
                    if self._name_attr2obj(attr) in list(self.section_map[section].keys()):
                        self.section_map[section][self._name_attr2obj(attr)] = cf.get(section, attr)

    def _dump_config(self):
        cf = CliConfigParser()
        for section in list(self.section_map.keys()):
            #当前用户的配置
            if section == UserConfig.USER_QCLOUD_CONFIG:
                curr_user = self.section_map[UserConfig.OTHERS]['curr_user']
                cf.add_section(curr_user)
                for key in list(self.section_map[section].keys()):
                    if self.section_map[section][key]:
                        cf.set(curr_user, self._name_obj2attr(key), self.section_map[section][key])
            #其他用户列表的配置
            elif section.startswith('USER_') and section != self.section_map[UserConfig.OTHERS]['curr_user']:
                cf.add_section(section)
                for key in list(self.section_map[UserConfig.USER_QCLOUD_CONFIG].keys()):
                    if self.section_map[section][key]:
                        cf.set(section, self._name_obj2attr(key), self.section_map[section][key])
            #公用配置
            elif section in UserConfig.COMMON_SECTION_LIST:
                cf.add_section(section)
                for key in list(self.section_map[section].keys()):
                    if self.section_map[section][key]:
                        cf.set(section, self._name_obj2attr(key), self.section_map[section][key])

        with open(_USER_CONFIG_FILE, "w") as f:
            cf.write(f)

    @staticmethod
    def _name_attr2obj(name):
        return name.replace("-", "_")

    @staticmethod
    def _name_obj2attr(name):
        return name.replace("_", "-")


if __name__ == '__main__':
    uc = UserConfig()
    # print uc.get_attrs({"secret-sssd": True, "region": False, "secret-key": "000000000"})
    # print uc.get_attrs({"secret-id": True, "region": True, "secret-key": "000000000"})
    # uc.set_attrs({"region":"asss-gz"})
    # uc.flush()
    print(uc.get_attrs({"region": True, "secret-key": "000000000"}))
