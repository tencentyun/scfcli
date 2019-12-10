from .tcsam_macro import TcSamMacro as macro

class TcSamutil(object):

    @staticmethod
    def merge_globals(tcsam_data):
        resources = tcsam_data.get(macro.Resources, {})
        glob = tcsam_data.get(macro.Globals, {})
        glob_func_proper = glob.get(macro.Function, {})

        if glob_func_proper is None:
            return

        for func in TcSamutil._iter_func(resources):
            if macro.Properties not in func:
                continue
            if func[macro.Properties] is None:
                func[macro.Properties] = {}
            for pro in glob_func_proper:
                # merge events
                if pro == macro.Events: 
                    if pro in func[macro.Properties]: 
                        for trigger in glob_func_proper[pro]:
                            glob_trigger_type = glob_func_proper[pro][trigger]['Type']
                            found = False
                            for func_trigger in func[macro.Properties][pro]:
                                func_trigger_type = func[macro.Properties][pro][func_trigger]['Type']
                                if func_trigger_type == glob_trigger_type:
                                    found = True

                            if found == False:
                                func[macro.Properties][pro][trigger] = glob_func_proper[pro][trigger]

                    else:
                        func[macro.Properties][pro] = glob_func_proper[pro]
                # merge env
                elif pro == macro.Envi:
                    if pro in glob_func_proper and macro.Vari in glob_func_proper[pro]:
                        if pro not in func[macro.Properties] or func[macro.Properties][pro] == None:
                            func[macro.Properties][pro] = {}
                        if macro.Vari not in func[macro.Properties][pro] or func[macro.Properties][pro][macro.Vari] == None:
                            func[macro.Properties][pro] = {
                                macro.Vari: {}
                            }

                        for vkey in glob_func_proper[pro][macro.Vari]:
                            if vkey not in func[macro.Properties][pro][macro.Vari]:
                                func[macro.Properties][pro][macro.Vari][vkey] = glob_func_proper[pro][macro.Vari][vkey]

                elif pro not in func[macro.Properties] and glob_func_proper[pro]:
                    func[macro.Properties][pro] = glob_func_proper[pro]


    @staticmethod
    def _iter_func(resources):
        for ns in resources:
            if resources[ns] is None:
                continue
            for func in resources[ns]:
                if func == macro.Type or resources[ns][func] is None:
                    continue
                yield resources[ns][func]
