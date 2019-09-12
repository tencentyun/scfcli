# -*- coding: utf-8 -*-

import os
import platform
from tcfcli.common.user_exceptions import *

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
        self.version_time = "None"

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
               "version_time": "None",
               "no_color": "False",
               "language": "None",
               "allow_report": "True",
            }
        }

        self._migrate()
        self._load_config()
        self._dumpattr()

    # 新老配置迁移函数
    def _migrate(self):
        cf = CliConfigParser()
        cf.read(_USER_CONFIG_FILE)
        # 读取旧的section数据
        if UserConfig.API in cf.sections():
            attrs = {}
            for attrs_keys in cf.options(UserConfig.API):
                attrs[self._name_attr2obj(attrs_keys)] = cf.get(UserConfig.API, attrs_keys)
            self.set_attrs(attrs)
            self.section_map[UserConfig.OTHERS]['curr_user'] = 'USER_'+str(1)
            self._dump_config()

    def _dumpattr(self):
        self.secret_id = self.section_map[UserConfig.USER_QCLOUD_CONFIG]['secret_id']
        self.secret_key = self.section_map[UserConfig.USER_QCLOUD_CONFIG]['secret_key']
        self.region = self.section_map[UserConfig.USER_QCLOUD_CONFIG]['region']
        self.appid = self.section_map[UserConfig.USER_QCLOUD_CONFIG]['appid']
        self.using_cos = self.section_map[UserConfig.USER_QCLOUD_CONFIG]['using_cos']
        self.python2_path = self.section_map[UserConfig.ENV]['python2_path']
        self.python3_path = self.section_map[UserConfig.ENV]['python3_path']
        self.version_time = self.section_map[UserConfig.OTHERS]['version_time']

    def set_attrs(self, attrs):
        for section in self.section_map:
            # 只设置当前用户和公共配置
            if section not in UserConfig.SECTION_LIST:
                continue
            for key in list(self.section_map[section].keys()):
                # 更新section_map中存在的配置变量
                if key in list(attrs.keys()) and attrs[key]:
                    self.section_map[section][key] = attrs[key]

    def get_attrs(self, attrs):
        ret = {}
        for attr_key in [k for k, v in attrs.items() if v]:
            for section in self.section_map:
                if section not in UserConfig.SECTION_LIST:
                    continue
                if self._name_attr2obj(attr_key) in self.section_map[section].keys():
                    ret[self._name_attr2obj(attr_key)] = self.section_map[section][self._name_attr2obj(attr_key)]
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
        userlist = []
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
            if i >= 99:
                raise UserLimitException("Amount of Users Limit!")

        self.section_map[user_section] = {}
        format_data = {}
        for k in data:
            format_data[self._name_attr2obj(k)] = data[k]
        for key in list(self.section_map[UserConfig.USER_QCLOUD_CONFIG].keys()):
            if key in format_data and format_data[key]:
                self.section_map[user_section][key] = format_data[key]
            elif key == 'using_cos':
                self.section_map[user_section][key] = "False (By default, it isn't deployed by COS.)"
            else:
                self.section_map[user_section][key] = "None"
        return user_section

    def changeuser(self, user):
        self.section_map[UserConfig.OTHERS]['curr_user'] = user
        for key in list(self.section_map[UserConfig.USER_QCLOUD_CONFIG].keys()):
            self.section_map[UserConfig.USER_QCLOUD_CONFIG][key] = self.section_map[user][key]

    def get_user_info(self, user):
        data = {}
        data['appid'] = self.section_map[user]['appid']
        data['secret_id'] = self.section_map[user]['secret_id']
        data['secret_key'] = self.section_map[user]['secret_key']
        data['region'] = self.section_map[user]['region']
        data['using_cos'] = self.section_map[user]['using_cos']
        return data

    def _load_config(self):
        cf = CliConfigParser()
        if not cf.read(_USER_CONFIG_FILE):
            return
        # 从配置文件获取当前用户
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
            # 获取所有用户配置到对象
            if section.startswith('USER_'):
                self.section_map[section] = {}
                for key in list(self.section_map[UserConfig.USER_QCLOUD_CONFIG].keys()):
                    if self._name_obj2attr(key) in attrs:
                        self.section_map[section][key] = cf.get(section, self._name_obj2attr(key))
                    else:
                        self.section_map[section][key] = 'None'
            # 获取共有配置到对象
            else:
                for attr in attrs:
                    if self._name_attr2obj(attr) in list(self.section_map[section].keys()):
                        self.section_map[section][self._name_attr2obj(attr)] = cf.get(section, attr)

    def _dump_config(self):
        cf = CliConfigParser()
        # 保证先遍历到USER_QCLOUD_CONFIG
        for section in sorted(list(self.section_map.keys()), reverse=True):
            # 当前用户的配置
            if section == UserConfig.USER_QCLOUD_CONFIG:
                curr_user = self.section_map[UserConfig.OTHERS]['curr_user']
                # 当前用户非User_开头，强制修正为user_1
                if not curr_user.startswith('USER_'):
                    self.section_map[UserConfig.OTHERS]['curr_user'] = 'USER_1'
                    curr_user = 'USER_1'
                cf.add_section(curr_user)
                for key in list(self.section_map[section].keys()):
                    if self.section_map[section][key]:
                        cf.set(curr_user, self._name_obj2attr(key), self.section_map[section][key])
            # 其他用户列表的配置
            elif section.startswith('USER_') and section != self.section_map[UserConfig.OTHERS]['curr_user']:
                cf.add_section(section)
                for key in list(self.section_map[UserConfig.USER_QCLOUD_CONFIG].keys()):
                    if self.section_map[section][key]:
                        cf.set(section, self._name_obj2attr(key), self.section_map[section][key])
            # 公用配置
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
