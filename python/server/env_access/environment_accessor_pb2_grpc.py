# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from . import environment_accessor_pb2 as environment__accessor__pb2


class EnvironmentAccessorStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.getObject = channel.unary_stream(
        '/abc.EnvironmentAccessor/getObject',
        request_serializer=environment__accessor__pb2.ObjectRetrievalRequest.SerializeToString,
        response_deserializer=environment__accessor__pb2.ObjectRetrievalResponse.FromString,
        )


class EnvironmentAccessorServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def getObject(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_EnvironmentAccessorServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'getObject': grpc.unary_stream_rpc_method_handler(
          servicer.getObject,
          request_deserializer=environment__accessor__pb2.ObjectRetrievalRequest.FromString,
          response_serializer=environment__accessor__pb2.ObjectRetrievalResponse.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'abc.EnvironmentAccessor', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
