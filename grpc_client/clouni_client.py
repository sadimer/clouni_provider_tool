
import six
import yaml
from yaml import Loader

from grpc_server.api_pb2 import ClouniProviderToolResponse, ClouniProviderToolRequest
import grpc_server.api_pb2_grpc as api_pb2_grpc
import grpc
import sys
import os
import argparse

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(prog="clouni-client")

    parser.add_argument('--template-file',
                        metavar='<filename>',
                        required=True,
                        help='YAML template to parse.')
    parser.add_argument('--cluster-name',
                        required=True,
                        help='Cluster name')
    parser.add_argument('--validate-only',
                        action='store_true',
                        default=False,
                        help='Only validate input template, do not perform translation.')
    parser.add_argument('--delete',
                        action='store_true',
                        default=False,
                        help='Delete cluster')
    parser.add_argument('--provider',
                        required=False,
                        help='Cloud provider name to execute ansible playbook in.')
    parser.add_argument('--output-file',
                        metavar='<filename>',
                        required=False,
                        help='Output file')
    parser.add_argument('--configuration-tool',
                        default="ansible",
                        help="Configuration tool which DSL the template would be translated to. "
                             "Default value = \"ansible\"")
    parser.add_argument('--extra',
                        default=[],
                        metavar="KEY=VALUE",
                        nargs='+',
                        help='Extra arguments for configuration tool scripts')
    parser.add_argument('--debug',
                        default=False,
                        action='store_true',
                        help='Set debug level for tool')
    parser.add_argument('--log-level',
                        default='info',
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='Set log level for tool')
    parser.add_argument('--host-parameter',
                        default='public_address',
                        help="Specify Compute property to be used as host IP for software components that hosted on the Compute. Valid values: public_address and private_address")
    parser.add_argument('--public-key-path',
                        default='~/.ssh/id_rsa.pub',
                        help="Set path to public key for configuration software on cloud servers")
    parser.add_argument('--host',
                        metavar='<host_name/host_address>',
                        default='localhost',
                        help='Host of server, default localhost')
    parser.add_argument('--port', '-p',
                        metavar='<port>',
                        default=50051,
                        type=int,
                        help='Port of server, default 50051')
    parser.add_argument('--configuration-tool-endpoint',
                        type=str,
                        help='Endpoint of configuration tool server')

    (args, args_list) = parser.parse_known_args(args)
    channel = grpc.insecure_channel(args.host + ':' + str(args.port))
    stub = api_pb2_grpc.ClouniProviderToolStub(channel)

    request = ClouniProviderToolRequest()

    template_file = os.path.join(os.getcwd(), args.template_file)
    with open(template_file, 'r') as f:
        template_content = f.read()
    request.template_file_content = template_content
    request.cluster_name = args.cluster_name
    request.validate_only = args.validate_only
    request.delete = args.delete
    if args.provider is not None:
        request.provider = args.provider
    else:
        request.provider = ""
    request.configuration_tool = args.configuration_tool
    request.log_level = args.log_level
    request.debug = args.debug
    request.host_parameter = args.host_parameter
    request.public_key_path = args.public_key_path
    if args.configuration_tool_endpoint is not None:
        request.configuration_tool_endpoint = args.configuration_tool_endpoint
    else:
        request.configuration_tool_endpoint = ""

    extra = {}
    for i in args.extra:
        i_splitted = [j.strip() for j in i.split('=', 1)]
        if len(i_splitted) < 2:
            raise Exception('Failed parsing parameter \'--extra\', required \'key=value\' format')
        extra.update({i_splitted[0]: i_splitted[1]})

    for k, v in extra.items():
        if isinstance(v, six.string_types):
            if v.isnumeric():
                if int(v) == float(v):
                    extra[k] = int(v)
                else:
                    extra[k] = float(v)

    request.extra = yaml.dump(extra)

    response = stub.ClouniProviderTool(request)
    print("* Status *\n")
    status = ['TEMPLATE_VALID', 'TEMPLATE_INVALID', 'OK', 'ERROR']
    print(status[response.status])
    print("\n* Error *\n")
    print(response.error)
    print("\n* Content *\n")
    print(response.content)