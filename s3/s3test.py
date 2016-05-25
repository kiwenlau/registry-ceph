import boto
import boto.s3.connection
access_key = 'ORPY7DJH3CI2GIQO8AC6'
secret_key = '6qrfsa4Tzn0R9KqsSZDq9bMiejZ8dZaUYjGhtdqh'
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
