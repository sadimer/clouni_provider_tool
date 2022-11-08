
import yaml
from yaml import Loader

from grpc_server.api_pb2 import ClouniProviderToolResponse, ClouniProviderToolRequest, ClouniConfigurationToolRequest
import grpc_server.api_pb2_grpc as api_pb2_grpc
from provider_tool.common.translator_to_configuration_dsl import translate

from provider_tool.common.utils import NoAliasDumper
from toscaparser.common.exception import ValidationError
from concurrent import futures
import logging
import grpc
import argparse
import sys
import atexit
import os
import six
import signal
from time import sleep, time
from functools import partial

SEPARATOR = ':'


def exit_gracefully(server, logger, x, y):
    server.stop(None)
    logger.info("Server stopped")
    print("Server stopped")
    sys.exit(0)


class TranslatorServer(object):
    def __init__(self, argv):
        self.template_file_content = argv['template_file_content']
        self.configuration_tool_endpoint = argv['configuration_tool_endpoint']
        self.database_api_endpoint = argv['database_api_endpoint']
        self.grpc_cotea_endpoint = argv['grpc_cotea_endpoint']
        self.cluster_name = argv['cluster_name']
        self.is_delete = argv['delete']
        self.provider = argv['provider']
        self.validate_only = argv['validate_only']
        self.configuration_tool = argv['configuration_tool']
        self.extra = argv['extra']
        self.log_level = argv['log_level']
        self.debug = False
        if argv['debug']:
            self.debug = True
            self.log_level = 'debug'
        self.host_parameter = argv['host_parameter']
        self.public_key_path = argv['public_key_path']

        if self.extra:
            self.extra = yaml.load(self.extra, Loader=Loader)

        for k, v in self.extra.items():
            if isinstance(v, six.string_types):
                if v.isnumeric():
                    if int(v) == float(v):
                        self.extra[k] = int(v)
                    else:
                        self.extra[k] = float(v)
                if v == 'true':
                    self.extra[k] = True
                if v == 'false':
                    self.extra[k] = False

        self.working_dir = os.getcwd()
        dict_tpl, extra = translate(self.template_file_content, self.validate_only, self.provider,
                                                   self.configuration_tool, self.cluster_name,
                                                   public_key_path=self.public_key_path,
                                                   host_ip_parameter=self.host_parameter, is_delete=self.is_delete,
                                                   extra={'global': self.extra}, log_level=self.log_level, a_file=False,
                                                   grpc_cotea_endpoint=self.grpc_cotea_endpoint)
        self.output = yaml.dump(dict_tpl, Dumper=NoAliasDumper)
        self.extra = yaml.dump(extra, Dumper=NoAliasDumper)
        if self.configuration_tool_endpoint and not self.validate_only:
            request = ClouniConfigurationToolRequest()
            request.provider_template = self.output
            request.cluster_name = self.cluster_name
            request.delete = self.is_delete
            request.configuration_tool = self.configuration_tool
            request.extra = self.extra
            request.log_level = self.log_level
            if self.database_api_endpoint is not None:
                request.database_api_endpoint = self.database_api_endpoint
            else:
                request.database_api_endpoint = ""
            if self.grpc_cotea_endpoint is not None:
                request.grpc_cotea_endpoint = self.grpc_cotea_endpoint
            else:
                request.grpc_cotea_endpoint = ""
            request.debug = self.debug
            channel = grpc.insecure_channel(self.configuration_tool_endpoint)
            stub = api_pb2_grpc.ClouniConfigurationToolStub(channel)
            response = stub.ClouniConfigurationTool(request)
            self.output = response.content
            if response.error:
                raise Exception(response.error)



class ClouniProviderToolServicer(api_pb2_grpc.ClouniProviderToolServicer):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger

    def ClouniProviderTool(self, request, context):
        self.logger.info("Request received")
        self.logger.debug("Request content: %s", str(request))
        args = self._RequestParse(request)
        response = ClouniProviderToolResponse()
        try:
            if request.validate_only:
                self.logger.info("Validate only request - status TEMPLATE_VALID")
                response.status = ClouniProviderToolResponse.Status.TEMPLATE_VALID
            else:
                self.logger.info("Request - status OK")
                response.status = ClouniProviderToolResponse.Status.OK
            response.content = TranslatorServer(args).output

            self.logger.info("Response send")
            return response
        except ValidationError as err:
            self.logger.exception("\n")
            if request.validate_only:
                self.logger.info("Validate only request - status TEMPLATE_INVALID")
                response.status = ClouniProviderToolResponse.Status.TEMPLATE_INVALID
            else:
                response.status = ClouniProviderToolResponse.Status.ERROR
                self.logger.info("Request - status ERROR")
            response.error = str(err)
            self.logger.info("Response send")
            return response
        except Exception as err:
            self.logger.exception("\n")
            self.logger.info("Request - status ERROR")
            response.status = ClouniProviderToolResponse.Status.ERROR
            response.error = str(err)
            self.logger.info("Response send")
            return response


    def _RequestParse(self, request):
        args = {}
        if request.template_file_content == "":
            raise Exception("Request field 'template_file_content' is required")
        else:
            args["template_file_content"] = request.template_file_content
        if request.cluster_name == "":
            raise Exception("Request field 'cluster_name' is required")
        else:
            args["cluster_name"] = request.cluster_name
        if request.validate_only:
            args['validate_only'] = True
        else:
            args['validate_only'] = False
        if request.delete:
            args['delete'] = True
        else:
            args['delete'] = False
        if request.provider != "":
            args['provider'] = request.provider
        else:
            args['provider'] = None
        if request.configuration_tool_endpoint != "":
            args['configuration_tool_endpoint'] = request.configuration_tool_endpoint
        else:
            args['configuration_tool_endpoint'] = None
        if request.database_api_endpoint != "":
            args['database_api_endpoint'] = request.database_api_endpoint
        else:
            args['database_api_endpoint'] = None
        if request.grpc_cotea_endpoint != "":
            args['grpc_cotea_endpoint'] = request.grpc_cotea_endpoint
        else:
            args['grpc_cotea_endpoint'] = None
        if request.configuration_tool != "":
            args['configuration_tool'] = request.configuration_tool
        else:
            args['configuration_tool'] = 'ansible'
        if request.extra != "":
            args['extra'] = request.extra
        else:
            args['extra'] = None
        if request.host_parameter != "":
            args['host_parameter'] = request.host_parameter
        else:
            args['host_parameter'] = 'public_address'
        if request.public_key_path != "":
            args['public_key_path'] = request.public_key_path
        else:
            args['public_key_path'] = '~/.ssh/id_rsa.pub'
        if request.log_level != "":
            args['log_level'] = request.log_level
        else:
            args['log_level'] = 'info'
        if request.debug:
            args['debug'] = True
        else:
            args['debug'] = False
        return args


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="clouni-provider-tool")
    parser.add_argument('--max-workers',
                        metavar='<number of workers>',
                        default=10,
                        type=int,
                        help='Maximum of working gRPC threads, default 10')
    parser.add_argument('--host',
                        metavar='<host_name/host_address>',
                        action='append',
                        help='Hosts on which server will be started, may be more than one, default [::]')
    parser.add_argument('--port', '-p',
                        metavar='<port>',
                        default=50051,
                        type=int,
                        help='Port on which server will be started, default 50051')
    parser.add_argument('--verbose', '-v',
                        action='count',
                        default=3,
                        help='Logger verbosity, default -vvv')
    parser.add_argument('--no-host-error',
                        action='store_true',
                        default=False,
                        help='If unable to start server on host:port and this option used, warning will be logged instead of critical error')
    parser.add_argument('--stop',
                        action='store_true',
                        default=False,
                        help='Stops all working servers and exit')
    parser.add_argument('--foreground',
                        action='store_true',
                        default=False,
                        help='Makes server work in foreground')
    try:
        args, args_list = parser.parse_known_args(argv)
    except argparse.ArgumentError:
        logging.critical("Failed to parse arguments. Exiting")
        raise Exception("Failed to parse arguments. Exiting")
    return args.max_workers, args.host, args.port, args.verbose, args.no_host_error, args.stop, args.foreground


def serve(argv =  None):
    # Log init
    logger = logging.getLogger("ClouniProviderTool server")
    fh = logging.FileHandler(".clouni-provider-tool.log")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    atexit.register(lambda logger: logger.info("Exited"), logger)
    # Argparse
    if argv is None:
        argv = sys.argv[1:]
    max_workers, hosts, port, verbose, no_host_error, stop, foreground = parse_args(argv)
    if stop:
        try:
            with open("/tmp/.clouni-provider-tool.pid", mode='r') as f:
                for line in f:
                    try:
                        os.kill(int(line), signal.SIGTERM)
                    except ProcessLookupError as e:
                        print(e)
            os.remove("/tmp/.clouni-provider-tool.pid")
        except FileNotFoundError:
            print("Working servers not found: no .clouni-provider-tool.pid file in this directory")
        sys.exit(0)
    if not foreground:
        if os.fork():
            sleep(1)
            os._exit(0)

    # Verbosity choose
    if verbose == 1:
        logger.info("Logger level set to ERROR")
        logger.setLevel(logging.ERROR)
    elif verbose == 2:
        logger.info("Logger level set to WARNING")
        logger.setLevel(logging.WARNING)
    elif verbose == 3:
        logger.info("Logger level set to INFO")
        logger.setLevel(logging.INFO)
    else:
        logger.info("Logger level set to DEBUG")
        logger.setLevel(logging.DEBUG)

    if hosts is None:
        hosts = ['[::]', ]
    logger.info("Logging clouni-provider-tool started")
    logger.debug("Arguments successfully parsed: max_workers %s, port %s, host %s", max_workers, port, str(hosts))
    # Argument checkа
    if max_workers < 1:
        logger.critical("Invalid max_workers argument: should be greater than 0. Exiting")
        raise Exception("Invalid max_workers argument: should be greater than 0. Exiting")
    if port == 0:
        logger.warning("Port 0 given - port will be runtime chosen - may be an error")
    if port < 0:
        logger.critical("Invalid port argument: should be greater or equal than 0. Exiting")
        raise Exception("Invalid port argument: should be greater or equal than 0. Exiting")
    # Starting server
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
        api_pb2_grpc.add_ClouniProviderToolServicer_to_server(
            ClouniProviderToolServicer(logger), server)
        host_exist = False
        for host in hosts:
            try:
                port = server.add_insecure_port(host+":"+str(port))
                host_exist = True
                logger.info("Server is going to start on %s:%s", host, port)
            except:
                if no_host_error:
                    logger.warning("Failed to start server on %s:%s", host, port)
                else:
                    logger.error("Failed to start server on %s:%s", host, port)
                    raise Exception("Failed to start server on %s:%s", host, port)
            if host_exist:
                with open("/tmp/.clouni-provider-tool.pid", mode='a') as f:
                    f.write(str(os.getpid()) + '\n')
                server.start()
                logger.info("Server started")
                print("Server started")
            else:
                logger.critical("No host exists")
                raise Exception("No host exists")
    except Exception:
        logger.critical("Unable to start the server")
        raise Exception("Unable to start the server")
    signal.signal(signal.SIGINT, partial(exit_gracefully, server, logger))
    signal.signal(signal.SIGTERM, partial(exit_gracefully, server, logger))
    while True:
        sleep(100)

if __name__ == '__main__':
    serve()
