# AwsS3Versioning
# extends GdsS3Client
# Checks to see if an S3 bucket has versioning enabled

from chalicelib.criteria.criteria_default import CriteriaDefault
from chalicelib.aws.gds_s3_client import GdsS3Client


class AwsS3Versioning(CriteriaDefault):

    active = True

    ClientClass = GdsS3Client

    resource_type = "AWS::S3::Bucket"

    is_regional = False

    title = "S3 Buckets: Bucket Versioning Enabled"
    description = "The following S3 bucket/s has/have versioning disabled"
    why_is_it_important = ("Versioning in S3 is a way to recover from unintended user changes and actions that might "
                           "occur through misuse or corruption, such as ransomware infection. Each time an object "
                           "changes, a new version of that object is created.")
    how_do_i_fix_it = ("Enable versioning on the s3 buckets listed above. Please see the following AWS documentation "
                       "to enable versioning for an S3 bucket:<br />"
                       "<a href='https://docs.aws.amazon.com/AmazonS3/latest/user-guide/enable-versioning.html'>"
                       "https://docs.aws.amazon.com/AmazonS3/latest/user-guide/enable-versioning.html</a>")

    def __init__(self, app):
        super(AwsS3Versioning, self).__init__(app)

    def get_data(self, session, **kwargs):
        self.app.log.debug("Getting a list of buckets")
        buckets = self.client.get_bucket_list(session)
        for bucket in buckets:
            # Mutating items as I'm iterating over them again... Sorry
            bucket['Versioning'] = self.client.get_bucket_versioning(session, bucket['Name'])

        return buckets

    def translate(self, data):
        item = {
            "resource_id": data.get('Name', ''),
            "resource_name": "arn:aws:s3:::" + data.get('Name', '')
        }

        return item

    def evaluate(self):
        pass
