import setuptools

reqs = ['six', 'grpcio==1.37.1', 'grpcio-tools==1.37.1', 'pyyaml', 'graphlib_backport', 'tosca-parser@git+https://github.com/sadimer/tosca-parser.git@1e95e27a7bc11f4dee8b8ded7c4db19a245a4d98']
setuptools.setup(install_requires=reqs)