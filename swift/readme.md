##Use Ceph as the Storage Driver for Docker Registry through Swift API 

- Run ceph within docker container based on **kiwenlau/ceph-demo** image
- Run docker registry within docker container based on **kiwenlau/registry:2.4.1** image

**1. Configure Docker**

```
sudo vim /etc/default/docker
```

**docker registry will listen on port 6000**

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

**3. Configure Ceph**

Create user

```
sudo docker exec ceph-demo radosgw-admin user create --uid="kiwenlau" --display-name="kiwenlau"
```

Creat subuser

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
            "access_key": "7HOTQULR1L5MC5FAS5L9",
            "secret_key": "b2G6ItcLcQEXNUV0cJ4HZmoEAqibYR1xTr51A3wR"
        }
    ],
    "swift_keys": [
        {
            "user": "kiwenlau:swift",
            "secret_key": "H5ZBBAI5GVZPa88acJu0eovdwkRSfxqmsYZS3C8j"
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

install [python-swiftclient](https://github.com/openstack/python-swiftclient)

```
sudo apt-get install python-setuptoolssudo easy_install pipsudo pip install --upgrade setuptoolssudo pip install --upgrade python-swiftclient
```

create registry container

```
swift -A http://127.0.0.1/auth/v1.0 -U kiwenlau:swift -K 'H5ZBBAI5GVZPa88acJu0eovdwkRSfxqmsYZS3C8j' post registry
```

list registry container

```
swift -A http://127.0.0.1/auth/v1.0 -U kiwenlau:swift -K 'H5ZBBAI5GVZPa88acJu0eovdwkRSfxqmsYZS3C8j' list
```

output:

```
registry
```

**4. Run Docker registry within Docker container**

```
vim config.yml
```

Please replace **password**

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
    password: 2y1rdwUggpMjPbpl5iwErnqPRJOAGmDbGSvefmWU 
    authurl: http://127.0.0.1/auth/v1.0
    tenantid: kiwenlau
    insecureskipverify: false
    container: registry
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

**5. Push image to docker registry**

```
sudo docker pull busybox
sudo docker tag busybox 127.0.0.1:6000/busybox
sudo docker push 127.0.0.1:6000/busybox
```
