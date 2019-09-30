from tcfcli.common.gitignore import MATCH_IGNORE, IgnoreList

ignore = IgnoreList()
ignore.parse(["*.tar.gz"])
print(ignore.match('./dist/module-1.0.0.tar.gz') == MATCH_IGNORE)