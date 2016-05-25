I want to use Ceph as the storage driver for docker registry, however, I failed to do it with Ceph S3 API. I use Ubuntu 14.04 and run both Ceph and Docker registry within Docker containers based on ceph/demo and registry:2.4.1 image. Steps to reproduce it described as follows:

**1. Configure Docker**

```
sudo vim /etc/default/docker
```

Docker registry will listen on port 6000

```
DOCKER_OPTS="-H unix:///var/run/docker.sock --insecure-registry 127.0.0.1:6000"
```

```
sudo restart docker
```

**2. Run Ceph within Docker container**

```
sudo docker run -d \
                -e MON_IP=127.0.0.1 \
                -e CEPH_NETWORK=127.0.0.0/24 \
                --net=host \
                --name=ceph-demo \
                ceph/demo
```

**3. Create a new Ceph User**

```
sudo docker exec ceph-demo radosgw-admin user create --uid="kiwenlau" --display-name="kiwenlau"
```

We can get **access_key** and **secret_key** from the output:

```
{
    "user_id": "kiwenlau",
    "display_name": "kiwenlau",
    "email": "",
    "suspended": 0,
    "max_buckets": 1000,
    "auid": 0,
    "subusers": [],
    "keys": [
        {
            "user": "kiwenlau",
            "access_key": "QBUP96T428H5RABDPPWY",
            "secret_key": "XIicy3UnEXyBdTAupWU9JMOKgrjA5l9jQu9RuIjw"
        }
    ],
    "swift_keys": [],
    "caps": [],
    "op_mask": "read, write, delete",
    "default_placement": "",
    "placement_tags": [],
    "bucket_quota": {
        "enabled": false,
        "max_size_kb": -1,
        "max_objects": -1
    },
    "user_quota": {
        "enabled": false,
        "max_size_kb": -1,
        "max_objects": -1
    },
    "temp_url_keys": []
}
```

**4. Create a new Ceph Bucket**

```
vim s3test.py
```

Please replace **access_key** and **secret_key**

```
import boto
import boto.s3.connection
access_key = 'XC5SVD9ZGQD0D0BG3J0H'
secret_key = 'uu3oqDZQjBFA22YqcuO4siuxecFVM0yYYHZ6COm4'
conn = boto.connect_s3(
aws_access_key_id = access_key,
aws_secret_access_key = secret_key,
host = "0.0.0.0",
is_secure=False,
calling_format = boto.s3.connection.OrdinaryCallingFormat(),
)
bucket = conn.create_bucket('docker-registry')
for bucket in conn.get_all_buckets():
        print "{name}\t{created}".format(
                name = bucket.name,
                created = bucket.creation_date,
)
```

```
python s3test.py
```

output:

```
docker-registry	2016-05-25T05:36:05.000Z
```

**5. Creat a new Swift User**

```
sudo docker exec ceph-demo radosgw-admin subuser create --uid=kiwenlau --subuser=kiwenlau:swift --access=full
```

output:

```
{
    "user_id": "kiwenlau",
    "display_name": "kiwenlau",
    "email": "",
    "suspended": 0,
    "max_buckets": 1000,
    "auid": 0,
    "subusers": [
        {
            "id": "kiwenlau:swift",
            "permissions": "full-control"
        }
    ],
    "keys": [
        {
            "user": "kiwenlau",
            "access_key": "QBUP96T428H5RABDPPWY",
            "secret_key": "XIicy3UnEXyBdTAupWU9JMOKgrjA5l9jQu9RuIjw"
        }
    ],
    "swift_keys": [
        {
            "user": "kiwenlau:swift",
            "secret_key": "DfwKCVUo7bCnXleTxbzymvRknoC5s8SfWIh4r2Sy"
        }
    ],
    "caps": [],
    "op_mask": "read, write, delete",
    "default_placement": "",
    "placement_tags": [],
    "bucket_quota": {
        "enabled": false,
        "max_size_kb": -1,
        "max_objects": -1
    },
    "user_quota": {
        "enabled": false,
        "max_size_kb": -1,
        "max_objects": -1
    },
    "temp_url_keys": []
}
```

Create secret key

```
sudo docker exec ceph-demo radosgw-admin key create --subuser=kiwenlau:swift --key-type=swift --gen-secret
```

output:

```
{
    "user_id": "kiwenlau",
    "display_name": "kiwenlau",
    "email": "",
    "suspended": 0,
    "max_buckets": 1000,
    "auid": 0,
    "subusers": [
        {
            "id": "kiwenlau:swift",
            "permissions": "full-control"
        }
    ],
    "keys": [
        {
            "user": "kiwenlau",
            "access_key": "QBUP96T428H5RABDPPWY",
            "secret_key": "XIicy3UnEXyBdTAupWU9JMOKgrjA5l9jQu9RuIjw"
        }
    ],
    "swift_keys": [
        {
            "user": "kiwenlau:swift",
            "secret_key": "oNWxGQO6kOGYlqgiM2p0NUWSAqf6MQ5OD2PB6h5E"
        }
    ],
    "caps": [],
    "op_mask": "read, write, delete",
    "default_placement": "",
    "placement_tags": [],
    "bucket_quota": {
        "enabled": false,
        "max_size_kb": -1,
        "max_objects": -1
    },
    "user_quota": {
        "enabled": false,
        "max_size_kb": -1,
        "max_objects": -1
    },
    "temp_url_keys": []
}
```

Test Swift Access:

```
swift -A http://127.0.0.1/auth/1.0 -U kiwenlau:swift -K 'oNWxGQO6kOGYlqgiM2p0NUWSAqf6MQ5OD2PB6h5E' list
```

output:

```
docker-registry
```

**6. Run Docker registry within Docker container**

```
vim config.yml
```

Please replace **access_key** and **secret_key**

```
version: 0.1
log:
  fields:
    service: registry
storage:
  cache:
    blobdescriptor: inmemory
  swift:
    username: kiwenlau:swift
    password: oNWxGQO6kOGYlqgiM2p0NUWSAqf6MQ5OD2PB6h5E
    authurl: http://127.0.0.1/auth/v1.0
    tenantid: kiwenlau
    insecureskipverify: false
    container: docker-registry
    rootdirectory: /registry
http:
    addr: :6000
    debug:
        addr: localhost:6001
    headers:
        X-Content-Type-Options: [nosniff]
health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3
```

Run docker registry within docker container

```
sudo docker run -d \
                -v `pwd`/config.yml:/etc/docker/registry/config.yml \
                --net=host \
                --name=docker-registry \
                registry:2.4.1
```

**7. Push image to docker registry**

```
sudo docker pull busyboxy
sudo docker tag busybox 127.0.0.1:6000/busybox
sudo docker push 127.0.0.1:6000/busybox
```
