# -*- coding: utf-8 -*-

import os
import platform

if platform.python_version() >= '3':
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser


class CliConfigParser(ConfigParser):
    def optionxform(self, optionstr):
        return optionstr


class StatisticsConfigure(object):

    def __init__(self):
        self.data_attr = ConfigParser()
        self.data_file = os.path.join(os.path.expanduser('~'), '.scf_statistics.ini')

    def read_data(self):
        if not os.path.isfile(self.data_file):
            self.write_data()
        self.data_attr.read(self.data_file)

    def write_data(self):
        self.data_attr.write(open(self.data_file, "w"))

    def delete_data(self):
        os.remove(self.data_file)

    def get_data(self, section=None, options=None):
        try:
            data = {}
            if section == None:
                for eve_section in self.data_attr.sections():
                    data[eve_section] = self.data_attr.items(eve_section)
            elif section != None and options == None:
                data[section] = self.data_attr.items(section)
            elif section != None and options != None:
                data[section] = self.data_attr.getint(section, options)
            return data
        except Exception as e:
            # self.delete_data()
            return False

    def set_data(self, section, options, value):
        try:
            if not self.data_attr.has_section(section) and section:  # 检查是否存在section
                self.data_attr.add_section(section)
            self.data_attr.set(section, options, value)
            return True
        except Exception as e:
            return False

    def get_args(self, input_args):
        try:
            command = []
            args = []
            is_command = True
            for eve_input in input_args[1:]:
                if not str(eve_input).startswith("-") and is_command:
                    command.append(eve_input)
                else:
                    is_command = False

                if is_command == False and str(eve_input).startswith("-"):
                    args.append(eve_input)

            section = " ".join(command)
            self.read_data()

            if not args:
                args.append("no_args")

            args.append("command_count")

            #print(section, args)
            for eve_args in args:
                #print(eve_args)
                try:
                    value = self.get_data(section, eve_args)
                    #print(value)
                    if value == False:
                        value = 0
                    else:
                        value = int(value[section])
                    value = value + 1
                    # print(value)
                    self.set_data(section, eve_args, str(value))
                except Exception as e:
                    pass
            self.write_data()
        except Exception as e:
            # print(e)
            pass
