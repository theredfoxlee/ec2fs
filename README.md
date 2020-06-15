# ec2fs

ec2fs is a simple FUSE interface for Amazaon EC2 service.

usage: `python3 -m ec2fs [-h] [-d] [--mock] [--background] [--region-name REGION_NAME] mount`

## Bigger picture

Amazon EC2 (Elastic Compute Cloud) allows users to create Virutal Machines on servers provided and maintained by Amazon Web Services.

Virtual Machines are created based on so called Amazon Machine Image.

User (mainly) can:

- create his own variation of Amazon Machine Images,
- create, launch, and terminate Virtual Machines.

Although, you can communicate with Amazon EC2 API directly (using raw XML documents), it's highly recommended to use one of its implementations in programming languages (.NET, C++, Go, Java, JavaScript, PHP, Python, Ruby).

**This project tries implements another way to communicate with Amazon EC2 API** - with using FUSE framework (that allows implementation of filesystems in the userspace).

## Usage

### Installation

**REQUIREMENTS** -> PYTHON 3.6+

``` bash
git clone https://github.com/theredfoxlee/ec2fs
pip3 install ec2fs
```

### Mounting

ec2fs have to connect to your Amazon EC2 account, **you have to export AWS security credentials before mounting** - otherwise it will fail to mount your account into a directory.

As an alternative, you can setup a playground using `--mock` flag - this will mock Amazon EC2 service, so no credentials are required.

```
python3 -m ec2fs [-h] [-d] [--mock] [--background] [--region-name REGION_NAME] mount

positional arguments:
  mount                 Empty directory where fs will be mounted.

optional arguments:
  -h, --help            show help message and exit
  -d, --debug           Turn on debug logging.
  --mock                Turn on ec2 mock.
  --background          Run as background process.
  --region-name REGION_NAME
```

### Endpoints

Files in ec2fs are:

- READ ONLY (cached metadata about resources)
- WRITE ONLY (mapped actions from Amazon EC2 Api)

---

[01] How to refresh list of instances from `instances/` directory?

``` bash
echo '{}' > ./actions/describe_instances
```

[02] How to refresh list of instances from `images/` directory?

```bash
echo '{}' > ./actions/describe_images
```

[03] How to create a few Virtual Machines?

``` bash
cat > ./actions/run_instances << 'END'
{
    "InstanceType": "t2.nano",
    "MaxCount": 5,
    "MinCount": 5,
    "ImageId": "ami-03cf127a"
}
END
```

[04] How to list all available actions?

``` bash
ls ./actions
```

[05] How to check cached state of a given instance?

```bash
jq .State ./instances/instance_id
```

[6] How to list all cached instances?

```bash
ls ./instances
```

[07] How to check cached state of a given image?

```bash
jq .State ./images/image_id
```

[08] How to list all cached images:

```bash
ls ./images
```

[09] How to list available small instance types?

```bash
grep small ./flavors
```

[10] How to see cached raw response from Amazon EC2 service?

``` bash
ja . requests/request_ida 
```

[11] How to list all cached responses:

```bash
ls ./requests
```

[12] How to terminate some instances?

```bash
cat > ./actions/run_instances << 'END'
{
    "InstanceIds": [instance_id, instance_id, ..]
}
END
```

## Development status

It's still in beta, bugs are likely - current version: `0.1.0`

### Testing

Tests are driven by pytest (including benchmark tests) which environment is being setup by tox, so to run tests exec following commands:

```bash
git clone https://github.com/theredfoxlee/ec2fs
cd ec2fs
tox
```
