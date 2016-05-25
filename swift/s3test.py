import boto
import boto.s3.connection
access_key = 'QBUP96T428H5RABDPPWY'
secret_key = 'XIicy3UnEXyBdTAupWU9JMOKgrjA5l9jQu9RuIjw'
conn = boto.connect_s3(
aws_access_key_id = access_key,
aws_secret_access_key = secret_key,
host = "127.0.0.1",
is_secure=False,
calling_format = boto.s3.connection.OrdinaryCallingFormat(),
)
bucket = conn.create_bucket('docker-registry')
for bucket in conn.get_all_buckets():
        print "{name}\t{created}".format(
                name = bucket.name,
                created = bucket.creation_date,
)
