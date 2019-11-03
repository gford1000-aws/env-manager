import argparse
import grpc
from env_access import EnvironmentAccessorStub, ObjectRetrievalRequest, ObjectRetrievalResponse

def print_object(stub, logical_bucket, key, version, chunk_size):
	"""
	Here just accumulate the response data and print in one go
	"""
	complete_data = ""
	err = None
	for resp in stub.getObject(
			ObjectRetrievalRequest(
				logical_location=logical_bucket, 
				object_key=key,
				object_version=version,
				part_size=chunk_size)):
		if resp.HasField('status'):
			# Encountered an error
			err = resp.status
			break
		else:
			complete_data = complete_data + resp.data

	if err:
		print(f"Caught error: id: {err.code}, message: {err.message}")
	else:
		print(complete_data)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Demo grpc client, retrieving objects from s3')
	parser.add_argument('--p', help='localhost port on which to listen', default=50053)
	parser.add_argument('--b', help='logical bucket name containing the object', default='LOCATION_A')
	parser.add_argument('--k', help='the key of the object to load', default='hello_world.txt')
	parser.add_argument('--v', type=int, help='the (integer) version of the object.  0 for latest', default=0)
	parser.add_argument('--s', type=int, help='chunk size for large object transfers', default=1024)
	args = parser.parse_args()

	try:
		with grpc.insecure_channel(f"localhost:{args.p}") as channel:
			print(f"Connected to server at localhost:{args.p}")
			stub = EnvironmentAccessorStub(channel)
			print_object(stub, args.b, args.k, args.v, args.s)

	except Exception as e:
		print(f"Error received: {e}")			
