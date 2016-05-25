I want to use Ceph as the storage driver for docker registry, however, I failed to do it. I use Ubuntu 14.04 and run both Ceph and Docker registry within Docker containers. Steps to reproduce it described as follows:

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
                -e MON_IP=192.168.59.1 \
                -e CEPH_NETWORK=192.168.59.0/24 \
                --net=host \
                --name=ceph-demo \
                ceph/demo
```

192.168.59.1 is the ip address of the host.

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
            "access_key": "XC5SVD9ZGQD0D0BG3J0H",
            "secret_key": "uu3oqDZQjBFA22YqcuO4siuxecFVM0yYYHZ6COm4"
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

**5. Run Docker registry within Docker container

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
  s3:
    region: default
    bucket: docker-registry
    accesskey: XC5SVD9ZGQD0D0BG3J0H
    secretkey: uu3oqDZQjBFA22YqcuO4siuxecFVM0yYYHZ6COm4
    regionendpoint: 192.168.59.1:80
    secure: false
http:
    addr: :6000
    headers:
        X-Content-Type-Options: [nosniff]
health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3
```

```
sudo docker run -d \
                -v `pwd`/config.yml:/etc/docker/registry/config.yml \
                --net=host \
                --name=docker-registry \
                registry:2.4.1
```

**6. Push image to docker registry(Failed..)**

```
sudo docker pull busyboxy
sudo docker tag busybox 127.0.0.1:6000/busybox
sudo docker push 127.0.0.1:6000/busybox
```

Output of "docker push"

```
The push refers to a repository [127.0.0.1:6000/busybox]
5f70bf18a086: Retrying in 1 second 
1834950e52ce: Retrying in 1 second 
received unexpected HTTP status: 503 Service Unavailable
```

```
sudo docker logs docker-registry
```

```
time="2016-05-24T12:37:34Z" level=warning msg="No HTTP secret provided - generated random secret. This may cause problems with uploads if multiple registries are behind a load-balancer. To provide a shared secret, fill in http.secret in the configuration file or set the REGISTRY_HTTP_SECRET environment variable." go.version=go1.6.2 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db version=v2.4.1 
time="2016-05-24T12:37:34Z" level=info msg="redis not configured" go.version=go1.6.2 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db version=v2.4.1 
time="2016-05-24T12:37:34Z" level=info msg="Starting upload purge in 18m0s" go.version=go1.6.2 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db version=v2.4.1 
time="2016-05-24T12:37:34Z" level=info msg="using inmemory blob descriptor cache" go.version=go1.6.2 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db version=v2.4.1 
time="2016-05-24T12:37:34Z" level=info msg="listening on [::]:6000" go.version=go1.6.2 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db version=v2.4.1 
time="2016-05-24T12:37:46Z" level=info msg="response completed" go.version=go1.6.2 http.request.host="127.0.0.1:6000" http.request.id=3052a1f1-e294-418d-a0f9-9d91354d2aac http.request.method=GET http.request.remoteaddr="127.0.0.1:52923" http.request.uri="/v2/" http.request.useragent="docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))" http.response.contenttype="application/json; charset=utf-8" http.response.duration="941.512µs" http.response.status=200 http.response.written=2 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db version=v2.4.1 
127.0.0.1 - - [24/May/2016:12:37:46 +0000] "GET /v2/ HTTP/1.1" 200 2 "" "docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))"
time="2016-05-24T12:37:46Z" level=error msg="response completed with error" err.code=unknown err.detail="s3aws: : \n\tstatus code: 400, request id: " err.message="unknown error" go.version=go1.6.2 http.request.host="127.0.0.1:6000" http.request.id=724dec9e-99e0-4b92-951a-6fed97dc6e07 http.request.method=POST http.request.remoteaddr="127.0.0.1:52925" http.request.uri="/v2/busybox/blobs/uploads/" http.request.useragent="docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))" http.response.contenttype="application/json; charset=utf-8" http.response.duration=1.801973ms http.response.status=500 http.response.written=117 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db vars.name=busybox version=v2.4.1 
127.0.0.1 - - [24/May/2016:12:37:46 +0000] "POST /v2/busybox/blobs/uploads/ HTTP/1.1" 500 117 "" "docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))"
time="2016-05-24T12:37:46Z" level=error msg="response completed with error" err.code=unknown err.detail="s3aws: : \n\tstatus code: 400, request id: " err.message="unknown error" go.version=go1.6.2 http.request.host="127.0.0.1:6000" http.request.id=583b4bf9-2605-410c-aae2-3e26741f2e34 http.request.method=POST http.request.remoteaddr="127.0.0.1:52924" http.request.uri="/v2/busybox/blobs/uploads/" http.request.useragent="docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))" http.response.contenttype="application/json; charset=utf-8" http.response.duration=44.249308ms http.response.status=500 http.response.written=117 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db vars.name=busybox version=v2.4.1 
127.0.0.1 - - [24/May/2016:12:37:46 +0000] "POST /v2/busybox/blobs/uploads/ HTTP/1.1" 500 117 "" "docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))"
time="2016-05-24T12:37:51Z" level=error msg="response completed with error" err.code=unknown err.detail="s3aws: : \n\tstatus code: 400, request id: " err.message="unknown error" go.version=go1.6.2 http.request.host="127.0.0.1:6000" http.request.id=46d4b34f-31ba-4da8-ab25-569c6cd3bd0e http.request.method=POST http.request.remoteaddr="127.0.0.1:52926" http.request.uri="/v2/busybox/blobs/uploads/" http.request.useragent="docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))" http.response.contenttype="application/json; charset=utf-8" http.response.duration=3.992116ms http.response.status=500 http.response.written=117 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db vars.name=busybox version=v2.4.1 
127.0.0.1 - - [24/May/2016:12:37:51 +0000] "POST /v2/busybox/blobs/uploads/ HTTP/1.1" 500 117 "" "docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))"
time="2016-05-24T12:37:51Z" level=error msg="response completed with error" err.code=unknown err.detail="s3aws: : \n\tstatus code: 400, request id: " err.message="unknown error" go.version=go1.6.2 http.request.host="127.0.0.1:6000" http.request.id=98a6c782-1be4-41a6-8df6-7c598466e850 http.request.method=POST http.request.remoteaddr="127.0.0.1:52927" http.request.uri="/v2/busybox/blobs/uploads/" http.request.useragent="docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))" http.response.contenttype="application/json; charset=utf-8" http.response.duration=1.914856ms http.response.status=500 http.response.written=117 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db vars.name=busybox version=v2.4.1 
127.0.0.1 - - [24/May/2016:12:37:51 +0000] "POST /v2/busybox/blobs/uploads/ HTTP/1.1" 500 117 "" "docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))"
time="2016-05-24T12:38:01Z" level=error msg="response completed with error" err.code=unknown err.detail="s3aws: : \n\tstatus code: 400, request id: " err.message="unknown error" go.version=go1.6.2 http.request.host="127.0.0.1:6000" http.request.id=820c94e8-d352-4ad6-8413-952624e36683 http.request.method=POST http.request.remoteaddr="127.0.0.1:52928" http.request.uri="/v2/busybox/blobs/uploads/" http.request.useragent="docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))" http.response.contenttype="application/json; charset=utf-8" http.response.duration=1.41775ms http.response.status=500 http.response.written=117 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db vars.name=busybox version=v2.4.1 
127.0.0.1 - - [24/May/2016:12:38:01 +0000] "POST /v2/busybox/blobs/uploads/ HTTP/1.1" 500 117 "" "docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))"
time="2016-05-24T12:38:01Z" level=error msg="response completed with error" err.code=unknown err.detail="s3aws: : \n\tstatus code: 400, request id: " err.message="unknown error" go.version=go1.6.2 http.request.host="127.0.0.1:6000" http.request.id=bbc0e15e-c1bd-44c8-88ef-835cc65d6c2f http.request.method=POST http.request.remoteaddr="127.0.0.1:52929" http.request.uri="/v2/busybox/blobs/uploads/" http.request.useragent="docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))" http.response.contenttype="application/json; charset=utf-8" http.response.duration=1.797906ms http.response.status=500 http.response.written=117 instance.id=f41bdd32-63d4-48b6-8910-92bca61e90db vars.name=busybox version=v2.4.1 
127.0.0.1 - - [24/May/2016:12:38:01 +0000] "POST /v2/busybox/blobs/uploads/ HTTP/1.1" 500 117 "" "docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))"
127.0.0.1 - - [24/May/2016:12:38:16 +0000] "POST /v2/busybox/blobs/uploads/ HTTP/1.1" 503 125 "" "docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))"
127.0.0.1 - - [24/May/2016:12:38:16 +0000] "POST /v2/busybox/blobs/uploads/ HTTP/1.1" 503 125 "" "docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))"
127.0.0.1 - - [24/May/2016:12:38:36 +0000] "POST /v2/busybox/blobs/uploads/ HTTP/1.1" 503 125 "" "docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))"
127.0.0.1 - - [24/May/2016:12:38:36 +0000] "POST /v2/busybox/blobs/uploads/ HTTP/1.1" 503 125 "" "docker/1.11.1 go/go1.5.4 git-commit/5604cbe kernel/3.16.0-30-generic os/linux arch/amd64 UpstreamClient(Docker-Client/1.11.1 \\(linux\\))"
```


```
sudo docker logs ceph-demo
```

```
creating /etc/ceph/ceph.client.admin.keyring
creating /etc/ceph/ceph.mon.keyring
monmaptool: monmap file /etc/ceph/ceph.monmap
monmaptool: set fsid to a1b0bb70-7054-4175-9246-e8bd2a3c627a
monmaptool: writing epoch 0 to /etc/ceph/ceph.monmap (1 monitors)
creating /tmp/ceph.mon.keyring
importing contents of /etc/ceph/ceph.client.admin.keyring into /tmp/ceph.mon.keyring
importing contents of /etc/ceph/ceph.mon.keyring into /tmp/ceph.mon.keyring
ceph-mon: set fsid to a1b0bb70-7054-4175-9246-e8bd2a3c627a
ceph-mon: created monfs at /var/lib/ceph/mon/ceph-macubuntu1 for mon.macubuntu1
set pool 0 size to 1
0
2016-05-24 12:12:02.967106 7fe02a207940 -1 journal FileJournal::_open: disabling aio for non-block journal.  Use journal_force_aio to force use of aio anyway
2016-05-24 12:12:02.990162 7fe02a207940 -1 journal FileJournal::_open: disabling aio for non-block journal.  Use journal_force_aio to force use of aio anyway
2016-05-24 12:12:02.991790 7fe02a207940 -1 filestore(/var/lib/ceph/osd/ceph-0) could not find -1/23c2fcde/osd_superblock/0 in index: (2) No such file or directory
2016-05-24 12:12:03.007930 7fe02a207940 -1 created object store /var/lib/ceph/osd/ceph-0 journal /var/lib/ceph/osd/ceph-0/journal for osd.0 fsid a1b0bb70-7054-4175-9246-e8bd2a3c627a
add item id 0 name 'osd.0' weight 1 at location {host=macubuntu1,root=default} to crush map
starting osd.0 at :/0 osd_data /var/lib/ceph/osd/ceph-0 /var/lib/ceph/osd/ceph-0/journal
starting osd.0 at :/0 osd_data /var/lib/ceph/osd/ceph-0 /var/lib/ceph/osd/ceph-0/journal
pool 'cephfs_data' created
pool 'cephfs_metadata' created
new fs with metadata pool 2 and data pool 1
starting mds.0 at :/0
2016-05-24 12:12:06.601035 7fa159c6b780 -1 deprecation warning: MDS id 'mds.0' is invalid and will be forbidden in a future version.  MDS names may not start with a numeric digit.
    cluster a1b0bb70-7054-4175-9246-e8bd2a3c627a
     health HEALTH_WARN
            80 pgs stuck inactive
            80 pgs stuck unclean
     monmap e1: 1 mons at {macubuntu1=192.168.59.1:6789/0}
            election epoch 2, quorum 0 macubuntu1
     mdsmap e2: 0/0/1 up
     osdmap e7: 1 osds: 1 up, 1 in
            flags sortbitwise
      pgmap v8: 80 pgs, 3 pools, 0 bytes data, 0 objects
            0 kB used, 0 kB / 0 kB avail
                  80 creating

2016-05-24 12:12:05.724506 mon.0 [INF] from='client.? 192.168.59.1:0/2545860913' entity='client.admin' cmd=[{"prefix": "osd pool create", "pg_num": 8, "pool": "cephfs_metadata"}]: dispatch
2016-05-24 12:12:06.178058 mon.0 [INF] from='client.? 192.168.59.1:0/2545860913' entity='client.admin' cmd='[{"prefix": "osd pool create", "pg_num": 8, "pool": "cephfs_metadata"}]': finished
2016-05-24 12:12:06.191848 mon.0 [INF] osdmap e6: 1 osds: 1 up, 1 in
2016-05-24 12:12:06.203291 mon.0 [INF] pgmap v7: 80 pgs: 80 creating; 0 bytes data, 0 kB used, 0 kB / 0 kB avail
2016-05-24 12:12:06.419462 mon.0 [INF] from='client.? 192.168.59.1:0/1574499037' entity='client.admin' cmd=[{"prefix": "fs new", "data": "cephfs_data", "fs_name": "cephfs", "metadata": "cephfs_metadata"}]: dispatch
2016-05-24 12:12:06.426546 mon.0 [INF] osdmap e7: 1 osds: 1 up, 1 in
2016-05-24 12:12:06.433240 mon.0 [INF] from='client.? 192.168.59.1:0/1574499037' entity='client.admin' cmd='[{"prefix": "fs new", "data": "cephfs_data", "fs_name": "cephfs", "metadata": "cephfs_metadata"}]': finished
2016-05-24 12:12:06.433472 mon.0 [INF] mdsmap e2: 0/0/1 up
2016-05-24 12:12:06.433539 mon.0 [INF] pgmap v8: 80 pgs: 80 creating; 0 bytes data, 0 kB used, 0 kB / 0 kB avail
2016-05-24 12:12:06.579856 mon.0 [INF] from='client.? 192.168.59.1:0/1685678940' entity='client.admin' cmd=[{"prefix": "auth get-or-create", "entity": "mds.0", "caps": ["mds", "allow", "osd", "allow *", "mon", "allow profile mds"]}]: dispatch
2016-05-24 12:12:06.583280 mon.0 [INF] from='client.? 192.168.59.1:0/1685678940' entity='client.admin' cmd='[{"prefix": "auth get-or-create", "entity": "mds.0", "caps": ["mds", "allow", "osd", "allow *", "mon", "allow profile mds"]}]': finished
2016-05-24 12:12:06.786749 mon.0 [INF] from='client.? 192.168.59.1:0/3444116782' entity='client.admin' cmd=[{"prefix": "auth get-or-create", "entity": "client.radosgw.gateway", "caps": ["osd", "allow rwx", "mon", "allow rw"]}]: dispatch
2016-05-24 12:12:06.790544 mon.0 [INF] from='client.? 192.168.59.1:0/3444116782' entity='client.admin' cmd='[{"prefix": "auth get-or-create", "entity": "client.radosgw.gateway", "caps": ["osd", "allow rwx", "mon", "allow rw"]}]': finished
 * Running on http://0.0.0.0:5000/
2016-05-24 12:12:07.798381 mon.0 [INF] osdmap e8: 1 osds: 1 up, 1 in
2016-05-24 12:12:07.800713 mon.0 [INF] pgmap v9: 88 pgs: 88 creating; 0 bytes data, 0 kB used, 0 kB / 0 kB avail
2016-05-24 12:12:08.822706 mon.0 [INF] osdmap e9: 1 osds: 1 up, 1 in
2016-05-24 12:12:08.877500 mon.0 [INF] pgmap v10: 88 pgs: 88 creating; 0 bytes data, 0 kB used, 0 kB / 0 kB avail
2016-05-24 12:12:09.815914 mon.0 [INF] osdmap e10: 1 osds: 1 up, 1 in
2016-05-24 12:12:09.821510 mon.0 [INF] pgmap v11: 96 pgs: 96 creating; 0 bytes data, 0 kB used, 0 kB / 0 kB avail
2016-05-24 12:12:10.820488 mon.0 [INF] mds.? 192.168.59.1:6804/399 up:boot
2016-05-24 12:12:10.822272 mon.0 [INF] mdsmap e3: 0/0/1 up, 1 up:standby
2016-05-24 12:12:10.827293 mon.0 [INF] osdmap e11: 1 osds: 1 up, 1 in
2016-05-24 12:12:10.831605 mon.0 [INF] pgmap v12: 96 pgs: 8 creating+peering, 88 active+clean; 848 bytes data, 9001 MB used, 17410 MB / 27849 MB avail; 1530 B/s wr, 1 op/s
2016-05-24 12:12:10.831752 mon.0 [INF] mdsmap e4: 1/1/1 up {0=0=up:creating}
2016-05-24 12:12:10.841829 mon.0 [INF] pgmap v13: 96 pgs: 8 creating+peering, 88 active+clean; 848 bytes data, 9001 MB used, 17410 MB / 27849 MB avail; 3033 B/s wr, 2 op/s
2016-05-24 12:12:11.841989 mon.0 [INF] mds.0 192.168.59.1:6804/399 up:active
2016-05-24 12:12:11.842255 mon.0 [INF] mdsmap e5: 1/1/1 up {0=0=up:active}
2016-05-24 12:12:11.852656 mon.0 [INF] osdmap e12: 1 osds: 1 up, 1 in
2016-05-24 12:12:11.921683 mon.0 [INF] pgmap v14: 104 pgs: 8 creating, 8 creating+peering, 88 active+clean; 848 bytes data, 9001 MB used, 17410 MB / 27849 MB avail
2016-05-24 12:12:12.853385 mon.0 [INF] osdmap e13: 1 osds: 1 up, 1 in
2016-05-24 12:12:12.912589 mon.0 [INF] pgmap v15: 112 pgs: 16 creating, 8 creating+peering, 88 active+clean; 848 bytes data, 9001 MB used, 17410 MB / 27849 MB avail
2016-05-24 12:12:13.864487 mon.0 [INF] osdmap e14: 1 osds: 1 up, 1 in
2016-05-24 12:12:13.872176 mon.0 [INF] pgmap v16: 120 pgs: 24 creating, 8 creating+peering, 88 active+clean; 848 bytes data, 9001 MB used, 17410 MB / 27849 MB avail
2016-05-24 12:12:14.881238 mon.0 [INF] osdmap e15: 1 osds: 1 up, 1 in
2016-05-24 12:12:14.895700 mon.0 [INF] pgmap v17: 128 pgs: 32 creating, 8 creating+peering, 88 active+clean; 848 bytes data, 9001 MB used, 17410 MB / 27849 MB avail
2016-05-24 12:12:15.898274 mon.0 [INF] osdmap e16: 1 osds: 1 up, 1 in
2016-05-24 12:12:15.900279 mon.0 [INF] pgmap v18: 128 pgs: 32 creating, 8 creating+peering, 88 active+clean; 848 bytes data, 9001 MB used, 17410 MB / 27849 MB avail
2016-05-24 12:12:16.907006 mon.0 [INF] osdmap e17: 1 osds: 1 up, 1 in
2016-05-24 12:12:16.914131 mon.0 [INF] pgmap v19: 136 pgs: 40 creating, 8 creating+peering, 88 active+clean; 848 bytes data, 9001 MB used, 17410 MB / 27849 MB avail
2016-05-24 12:12:17.916654 mon.0 [INF] osdmap e18: 1 osds: 1 up, 1 in
2016-05-24 12:12:17.919297 mon.0 [INF] pgmap v20: 136 pgs: 40 creating, 8 creating+peering, 88 active+clean; 848 bytes data, 9001 MB used, 17410 MB / 27849 MB avail
2016-05-24 12:12:22.313839 mon.0 [INF] pgmap v21: 136 pgs: 136 active+clean; 3142 bytes data, 9004 MB used, 17407 MB / 27849 MB avail; 60302 B/s rd, 1706 B/s wr, 155 op/s
2016-05-24 12:14:22.369975 mon.0 [INF] pgmap v22: 136 pgs: 136 active+clean; 3142 bytes data, 9004 MB used, 17407 MB / 27849 MB avail
2016-05-24 12:16:22.433355 mon.0 [INF] pgmap v23: 136 pgs: 136 active+clean; 3142 bytes data, 9004 MB used, 17407 MB / 27849 MB avail
2016-05-24 12:18:22.490436 mon.0 [INF] pgmap v24: 136 pgs: 136 active+clean; 3142 bytes data, 9005 MB used, 17407 MB / 27849 MB avail
2016-05-24 12:20:22.553936 mon.0 [INF] pgmap v25: 136 pgs: 136 active+clean; 3142 bytes data, 9005 MB used, 17407 MB / 27849 MB avail
2016-05-24 12:20:42.569943 mon.0 [INF] pgmap v26: 136 pgs: 136 active+clean; 3142 bytes data, 9005 MB used, 17407 MB / 27849 MB avail
2016-05-24 12:21:25.756605 mon.0 [INF] osdmap e19: 1 osds: 1 up, 1 in
2016-05-24 12:21:25.763029 mon.0 [INF] pgmap v27: 144 pgs: 8 creating, 136 active+clean; 3142 bytes data, 9005 MB used, 17407 MB / 27849 MB avail
2016-05-24 12:21:26.765384 mon.0 [INF] osdmap e20: 1 osds: 1 up, 1 in
2016-05-24 12:21:26.767327 mon.0 [INF] pgmap v28: 144 pgs: 8 creating, 136 active+clean; 3142 bytes data, 9005 MB used, 17407 MB / 27849 MB avail
2016-05-24 12:21:31.601357 mon.0 [INF] pgmap v29: 144 pgs: 144 active+clean; 3502 bytes data, 9005 MB used, 17407 MB / 27849 MB avail; 2805 B/s rd, 350 B/s wr, 5 op/s
2016-05-24 12:22:16.621455 mon.0 [INF] pgmap v30: 144 pgs: 144 active+clean; 3502 bytes data, 9005 MB used, 17406 MB / 27849 MB avail; 8665 B/s rd, 0 B/s wr, 14 op/s
2016-05-24 12:24:16.691440 mon.0 [INF] pgmap v31: 144 pgs: 144 active+clean; 3502 bytes data, 9006 MB used, 17406 MB / 27849 MB avail
2016-05-24 12:26:16.751221 mon.0 [INF] pgmap v32: 144 pgs: 144 active+clean; 3502 bytes data, 9006 MB used, 17406 MB / 27849 MB avail
2016-05-24 12:28:16.814587 mon.0 [INF] pgmap v33: 144 pgs: 144 active+clean; 3502 bytes data, 9006 MB used, 17406 MB / 27849 MB avail
2016-05-24 12:29:06.839429 mon.0 [INF] pgmap v34: 144 pgs: 144 active+clean; 3502 bytes data, 9006 MB used, 17406 MB / 27849 MB avail
2016-05-24 12:31:06.906320 mon.0 [INF] pgmap v35: 144 pgs: 144 active+clean; 3502 bytes data, 9006 MB used, 17406 MB / 27849 MB avail
2016-05-24 12:32:16.949336 mon.0 [INF] pgmap v36: 144 pgs: 144 active+clean; 3502 bytes data, 9006 MB used, 17406 MB / 27849 MB avail; 5570 B/s rd, 0 B/s wr, 9 op/s
2016-05-24 12:34:17.018840 mon.0 [INF] pgmap v37: 144 pgs: 144 active+clean; 3502 bytes data, 9006 MB used, 17405 MB / 27849 MB avail
2016-05-24 12:36:17.096526 mon.0 [INF] pgmap v38: 144 pgs: 144 active+clean; 3502 bytes data, 9006 MB used, 17405 MB / 27849 MB avail
2016-05-24 12:37:27.132318 mon.0 [INF] pgmap v39: 144 pgs: 144 active+clean; 3502 bytes data, 9006 MB used, 17405 MB / 27849 MB avail
2016-05-24 12:39:27.205386 mon.0 [INF] pgmap v40: 144 pgs: 144 active+clean; 3502 bytes data, 9006 MB used, 17405 MB / 27849 MB avail
```

 





    
