# aggregators for collating stats across teams and across audit criteria


class Collator():

    def __init__(self, app=None, dbh=None):
        self.app = app
        self.dbh = dbh

    def set_database_handle(self, dbh):
        self.dbh = dbh

    def get_default_audit_stats(self):
        return {
            "active_criteria": 0,
            "criteria_processed": 0,
            "criteria_passed": 0,
            "criteria_failed": 0,
            "issues_found": 0
        }


    def get_default_criteria_stats(self):
        return {
            "resources": 0,
            "tested": 0,
            "passed": 0,
            "failed": 0,
            "ignored": 0
        }


    def get_latest_audit(self, account_id):

        try:
            AccountAudit = self.dbh.get_model("AccountAudit")
            AccountLatestAudit = self.dbh.get_model("AccountLatestAudit")
            query = (
                AccountAudit.select()
                    .join(AccountLatestAudit)
                    .where(AccountLatestAudit.account_subscription_id == account_id))

            latest = query.get()
            self.app.log.debug("Found latest audit: " + self.app.utilities.to_json(latest.serialize()))

        except AccountLatestAudit.DoesNotExist as err:
            latest = None
            self.app.log.debug("Failed to get latest audit: " + str(err))

        return latest


    def get_team_stats(self, team_accounts):

        team_stats = self.get_default_audit_stats()

        for account in team_accounts:

            if account.active:

                latest = self.get_latest_audit(account.id)

                if latest is not None:
                    latest_data = latest.serialize()

                    self.app.log.debug("Latest audit: " + self.app.utilities.to_json(latest_data))

                    for stat in team_stats:
                        team_stats[stat] += latest_data[stat]

                else:
                    self.app.log.error("Latest audit not found for account: " + account.id)

        return team_stats


    def get_criteria_stats(self, criteria, accounts, teams):

        criteria_stats = []
        for criterion in criteria:
            team_data = []
            account_data = []
            for team in teams:

                team_stats = self.get_default_criteria_stats()

                for account in accounts:

                    account_stats = self.get_default_criteria_stats()

                    self.app.log.debug('Team ID: ' + account.product_team_id.id)
                    if account.product_team_id.id == team.id:

                        latest = self.get_latest_audit(account.id)

                        audit_criteria = latest.audit_criteria

                        for audit_criterion in audit_criteria:

                            self.app.log.debug('Criterion ID: ' + audit_criterion.criterion_id.id)

                            if audit_criterion.criterion_id.id == criterion.id:
                                audit_criterion_stats = {
                                    "resources": audit_criterion.resources,
                                    "tested": audit_criterion.tested,
                                    "passed": audit_criterion.passed,
                                    "failed": audit_criterion.failed,
                                    "ignored": audit_criterion.ignored
                                }

                                for stat in account_stats:
                                    account_stats[stat] += audit_criterion_stats[stat]

                        account_data.append({
                            "account_subscription": account,
                            "stats": account_stats
                        })

                        for stat in team_stats:
                            team_stats[stat] += account_stats[stat]

                team_data.append({
                    "product_team": team,
                    "stats": team_stats
                })

            criteria_stats.append({
                "criterion": criterion,
                "product_teams": team_data,
                "account_subscriptions": account_data
            })

        return criteria_stats



