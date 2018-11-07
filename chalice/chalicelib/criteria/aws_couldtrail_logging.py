"""
implements aws::couldtrail::logging
"""

from chalicelib.criteria.criteria_default import CriteriaDefault


class AwsCouldtrailLogging(CriteriaDefault):
    """
    """

    def __init__(self, app):
        """
        """
        super(AwsCouldtrailLogging, self).__init__(app)
        self.active = True
        self.resource_type = 'AWS::Cloudtrail::Logging'
        self.check_id = 'vjafUGJ9H0'
        self.language = 'en'
        self.region = 'us-east-1'
        self.annotation = ''
        self.title = '''
            Existance and Activation of Cloudtrail Logging across all regions
        '''
        self.description = 'A trail has not been created for a region, or logging is turned off for the trail <TrailName>.'
        self.why_is_it_important = 'With CloudTrail you can log all the activity of your AWS account, including actions taken through the AWS Management Console, AWS SDKs, command line tools, and other AWS services. Cloudtrail logs are vital to performing security analysis and troubleshooting operational issues.'
        self.how_do_i_fix_it = '''Ensure that a trail is created with multi-region enabled in order to record events from all AWS regions. Further information can be found at the AWS documentation:

AWS Documentation: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html
AWS CLI: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-create-and-update-a-trail-by-using-the-aws-cli.html

If a trail was already created, ensure that logging is enabled.'''

    def get_data(self, session, **kwargs):
        """
        """
        return

    def translate(self, data={}):
        """
        """
        return {
            "resource_id": "root",
            "resource_name": "Root Account",
        }

    def evaluate(self, event, item, whitelist=[]):
        """
        The event parameter is the lambda dictionary triggering this criterion
        and must be passed unmodified to the return dictionary.
        The item parameter is the value of the result key of the
        support API method called describe_trusted_advisor_check_result.
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/support.html#Support.Client.describe_trusted_advisor_check_result
        """
        event = {}
        # logic to determine resource_id, compliance_type
        if item[
            'describe_trusted_advisor_check_result'
        ]['result']['status'] == 'ok':
            compliance_type = 'COMPLIANT'
        else:
            compliance_type = 'NON_COMPLIANT'
            self.annotation = '<p>STATUS: {}!</p>'.format(
                item['describe_trusted_advisor_check_result']['result'][
                    'status'
                ]
            )
            # optional warning/yellow information
            if item[
                'describe_trusted_advisor_check_result'
            ]['result']['status'] == 'warning':
                self.annotation += '<p>Last Delivery Error: {}</p>'.format(
                    item['get_trail_status']['LatestDeliveryError']
                )
            if len(item['describe_trails']['trailList']) == 0:
                self.annotation += '<p>There are no trails!</p>'
            else:  # construct trail list
                self.annotation += '<p>NON COMPLIANT TRAIL LIST:<ul>'
                for trail in item['describe_trails']['trailList']:
                    self.annotation += '''
                        <ol>The trail {} in the region {} failed.</ol>
                    '''.format(trail['Name'], trail['HomeRegion'])
                self.annotation += '</ul></p>'
        return self.build_evaluation(
            self.translate()['resource_id'],
            compliance_type,
            event,
            self.resource_type,
            self.annotation
        )
