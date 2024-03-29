# Access to S3 via gRPC rpc calls to a Docker image

Creates a Docker image which:

1. Initialises using AWS SSM Parameter Store parameters.

2. Starts a gRPC server that implements ```EnvironmentAccessor``` service, as defined in the ```protos``` folder.

3. On-demand retrieval of S3 objects from a logical bucket name.  If the bucket has versioning enabled, the objects can be retrieved via their version (returing the last version if no version is specified).

Executing the following command in the ```python``` folder creates an image called ```my-env-server```:

```docker build --tag my-env-server .```

To start a container locally based on the image, execute:

```docker run -it --name env_test -p 50053:50055 -v $HOME/.aws/credentials:/home/env_mgr/.aws/credentials:ro my-env-server```

This will start a container called ```env_test``` that assumes the local default AWS credentials (when running within AWS use IAM roles to provide AWS credentials), listening on ```localhost:50053```, and defaulting that the logical bucket mappings are available in Parameter Store at ```/EnvironmentManager/PoC1/LogicalMappings``` in region ```eu-west-1```.

The parameter hierarchy is expected to be:

```python
LogicalMappings
   |
   -- <Logical Mapping Name>
          |
	  |-- Region
          |-- Bucket
```

Here, ```Bucket``` is the name of the bucket, and ```Region``` is the AWS region in which the bucket was created.

## Client

An example client application is available in ```python/client```, demonstrating how the server can provide streamed responses 
for large objects and specific object versions. By default the client will attempt to connect to the gRPC server at ```localhost:50053```.

## Dockerfile

Builds the image based on the python3.7 alpine image as follows:

1. Installs g++ and build kit
2. Installs and builds python packages as specified in ```requirements.txt```
3. Removes g++ and build kit
4. Reinstalls libstdc++ so that gRPC shared library dependencies are available
5. Creates env_mgr group and env_mgr user
6. Switches to the env_mgr user
7. Copies executable code in ```python/server``` to ```/home/env_mgr/server```
8. Sets the working directory to ```/home/env_mgr/server```
9. Opens port 50055
10. Starts the server on port 50055 using the command ```python ./aws_env_server.py --p 50055```

## Licence

This project is released under the MIT license. See [LICENSE](LICENSE) for details.
