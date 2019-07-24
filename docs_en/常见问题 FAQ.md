## Installation related

### Setuptools version is too old

Performance: error in scf setup command: 'install_requires' must be a string or list of strings containing valid project/version requirement specifiers

Workaround: pip install -U setuptools

### The existing distutils installation package cannot be upgraded

Performance: Cannot uninstall 'PyYAML'. It is a distutils installed project and thus we cannot accurately determine which files belong to it which would lead to only a partial uninstall.

Solution: pip install -I PyYAML==xxx (see the specific version in requirements.txt)

## Usage related

### How to specify a function for local debugging when there are multiple function descriptions in the yaml configuration file

Performance: You must provide a function identifier (function's Logical ID in the template). Possible options in your template: ['xxxB', 'xxxA']

Workaround: Call the local invoke command with a function name, such as scf local invoke -t template.yaml xxxA

### [SSL: CERTIFICATE_VERIFY_FAILED] error occurred during deployment

Performance: When using deploy, the deployment function fails, and the [SSL: CERTIFICATE_VERIFY_FAILED] certificate validation error is reported.

The cause of the problem: In the environment of mac 10.12 + python 3.6 and above, python no longer reads the system path certificate, which causes the certificate to fail to be read. The SSL verification fails when the Tencent Cloud API is deployed.

Solution: In the python installation directory, execute the Install Certificates.command script, which will automatically install the certifi package to resolve the certificate issue.
