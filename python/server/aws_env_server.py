import argparse
from aws_utils import SSMParameterStore
import boto3
import botocore.config
from botocore.exceptions import ClientError
from concurrent import futures
from datetime import datetime
from env_access import EnvironmentAccessorServicer, add_EnvironmentAccessorServicer_to_server, ObjectRetrievalRequest, ObjectRetrievalResponse, Status
import grpc
import json
from uuid import uuid4

class Timer(object):
	"""
	Basic timer object
	"""
	def __init__(self):
		self._start = datetime.utcnow()
	def get_microseconds(self):
		return int((datetime.utcnow() - self._start).total_seconds() * 1000000)

class RequestLogger(object):
	"""
	Simple logger object
	"""
	def __init__(self, function_name, initial_message, logger=print):
		self._function_name = function_name
		self._timer = Timer()
		self._request_id = str(uuid4())
		self._logger = logger

		self.log(initial_message)

	def log(self, message):
		self._logger("{} {} {}: {}".format(self._function_name, self._request_id, self._timer.get_microseconds(), message))

class EnvironmentAccessor(EnvironmentAccessorServicer):
	"""
	Calls to S3 using boto3 to retrieve object
	"""
	def __init__(self, store):
		super().__init__()

		self._clients = {}
		self._store = store

	def _get_client_and_bucket(self, logical_bucket_name):
		"""
		Returns a boto3 client and bucket name, if known
		"""
		bucket_name = store[logical_bucket_name]['Bucket']
		region_name = store[logical_bucket_name]['Region']
		if not bucket_name:
			raise Exception(f"Unknown logical bucket name: {logical_bucket_name}")

		return (self._clients.setdefault(region_name, 
				boto3.client('s3', region_name, config=botocore.config.Config(s3={'addressing_style':'path'}))),
				bucket_name)

	def _get_object_version(self, client, bucket_name, key, version):
		"""
		Versions are provided as monotonic integers via grpc, but this is not how S3 manages versions.

		Where a version is specified, need to list the available versions of the object and return
		AWS S3's version id for the correct version, orderd by the LastModified datetime
		"""
		if version < 0:
			raise Exception("Invalid version requested")

		resp = client.list_object_versions(
				Bucket=bucket_name,
				KeyMarker=key[0:len(key)-2],
				MaxKeys=36)

		if not resp['Versions']:
			raise Exception("Key versions not found")

		versions = {}
		found_key = False
		for version_detail in resp['Versions']:
			if version_detail['Key'] == key:
				versions[version_detail['LastModified']] = version_detail['VersionId']
				found_key = True
			elif found_key:
				break # Moved to next key

		if not found_key:
			raise Exception("Key not found")

		last_dates = list(versions.keys())
		last_dates.sort()

		if version > len(last_dates):
			# This will be the case if version<>0 for a non-versioned bucket
			# or where a version is requested that doesn't exist
			raise Exception("Requested version not found")

		return versions[last_dates[version-1]]	
		

	def getObject(self, request, context):
		"""
		Retrieve the object at the bucket/key location
		"""
		try:
			logger = RequestLogger('getObject', f"{request.logical_location}://{request.object_key}:version={request.object_version}")

			# Get connection and bucket details
			try:
				client, bucket_name = self._get_client_and_bucket(request.logical_location)

				if request.object_version == 0:
					# Attempt to retrieve data for latest object from S3
					resp = client.get_object(
						Bucket=bucket_name,
						Key=request.object_key)
				else:
					# Find the S3 VersionId of the requested version
					version_id = self._get_object_version(
							client,
							bucket_name,
							request.object_key,
							request.object_version)

					logger.log(f"Mapped requested version {request.object_version} to {version_id}")

					# Attempt to retrieve the specified version from S3
					resp = client.get_object(
						Bucket=bucket_name,
						Key=request.object_key,
						VersionId=version_id)

				logger.log("Retrieved data")

				# Allow customisation of data chunks being yielded
				chunk_size = 1024
				if request.part_size > 1024:
					chunk_size = request.part_size
					logger.log(f"Requested to send data in chunks={chunk_size}")

				for chunk in resp['Body'].iter_chunks(chunk_size=chunk_size):
					yield ObjectRetrievalResponse(data=chunk)

			except ClientError as e:
				logger.log(f"S3 returned error: {e}")
				if e.response['Error']['Code'] == 'NoSuchKey':
					yield ObjectRetrievalResponse(status=Status(code=5, message="Specified object_key not found"))
				else:
					yield ObjectRetrievalResponse(status=Status(code=13, message="Internal server error"))
			except Exception as e:
				logger.log(f"Error retrieving object: {e}")
				yield ObjectRetrievalResponse(status=Status(code=13, message="Internal server error"))

		except Exception as e:
			print(e)
		finally:
			if logger:
				logger.log("Completed")
	

def serve(port, bucket_mappings, max_workers_count):
	"""
	Initialise the gRPC server
	"""
	server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers_count))
	add_EnvironmentAccessorServicer_to_server(EnvironmentAccessor(bucket_mappings), server)
	server.add_insecure_port(f"[::]:{port}")
	server.start()
	server.wait_for_termination()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Demo grpc server to retrieve objects from s3')
	parser.add_argument('--p', help='localhost port on which to listen', default=50053)
	parser.add_argument('--t', help='Max number of grpc thread workers', default=10)
	parser.add_argument('--r', help='Config AWS region', default="eu-west-1")
	parser.add_argument('--c', help='Logical bucket mappings prefix', default="EnvironmentManager/PoC1")
	args = parser.parse_args()

	print(f"Logical bucket config loaded from {args.r}:/{args.c}")
	store = SSMParameterStore(prefix=f"/{args.c}/LogicalBuckets", ssm_client=boto3.client('ssm', region_name=args.r))

	print(f"Listening on localhost:{args.p}")
	serve(args.p, store, args.t)
