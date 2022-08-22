# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import grpc_server.api_pb2 as api__pb2


class ClouniProviderToolStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ClouniProviderTool = channel.unary_unary(
                '/ClouniProviderTool/ClouniProviderTool',
                request_serializer=api__pb2.ClouniProviderToolRequest.SerializeToString,
                response_deserializer=api__pb2.ClouniProviderToolResponse.FromString,
                )


class ClouniProviderToolServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ClouniProviderTool(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ClouniProviderToolServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ClouniProviderTool': grpc.unary_unary_rpc_method_handler(
                    servicer.ClouniProviderTool,
                    request_deserializer=api__pb2.ClouniProviderToolRequest.FromString,
                    response_serializer=api__pb2.ClouniProviderToolResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'ClouniProviderTool', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ClouniProviderTool(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ClouniProviderTool(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ClouniProviderTool/ClouniProviderTool',
            api__pb2.ClouniProviderToolRequest.SerializeToString,
            api__pb2.ClouniProviderToolResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class ClouniConfigurationToolStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ClouniConfigurationTool = channel.unary_unary(
                '/ClouniConfigurationTool/ClouniConfigurationTool',
                request_serializer=api__pb2.ClouniConfigurationToolRequest.SerializeToString,
                response_deserializer=api__pb2.ClouniConfigurationToolResponse.FromString,
                )


class ClouniConfigurationToolServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ClouniConfigurationTool(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ClouniConfigurationToolServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ClouniConfigurationTool': grpc.unary_unary_rpc_method_handler(
                    servicer.ClouniConfigurationTool,
                    request_deserializer=api__pb2.ClouniConfigurationToolRequest.FromString,
                    response_serializer=api__pb2.ClouniConfigurationToolResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'ClouniConfigurationTool', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ClouniConfigurationTool(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ClouniConfigurationTool(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ClouniConfigurationTool/ClouniConfigurationTool',
            api__pb2.ClouniConfigurationToolRequest.SerializeToString,
            api__pb2.ClouniConfigurationToolResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
