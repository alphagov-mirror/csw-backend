const extend = require('util')._extend;
const templater = {
    format_date_string: function(str) {
        let match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/.exec(str);
        let dateObject = new Date(match[1], match[2]-1, match[3], match[4], match[5], match[6]);
        let options = {
            hour12: false,
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };
        return dateObject.toLocaleString("en-GB", options);
    },
    reference_aliases: function() {
        let aliases = {
            compliant: "passed",
            applicable: "tested",
            non_compliant: "failed",
            not_applicable: "ignored"
        }
        return aliases;
    },
    reference_statuses: function() {
        let statuses = [
            {
                id: 1,
                status_name: "Unknown"
            },
            {
                id: 2,
                status_name: "Pass"
            },
            {
                id: 3,
                status_name: "Fail"
            },
            {
                id: 4,
                status_name: "Exception"
            }
        ]
        return statuses;
    },
    find_status_by_id: function(id) {
        let statuses = this.reference_statuses();
        let status = statuses.find(function(item) {
            return item.id == id;
        });
        return status;
    },
    find_check_by_id: function(checks, checkId) {
        let check = checks.find(function(item) {
            return item.id == checkId;
        });
        return check;
    },
    component_check_summary: function(check) {
        let aliases = this.reference_aliases();
        let summary = {
            id: check.id,
            criterion_id: {
                criterion_name: check.title,
                id: check.id
            }
        };
        for (key in aliases) {
            let alias = aliases[key];
            summary[alias] = check.summary[key]['display_stat'];
        }
        return summary;
    },
    find_resources_by_status: function(resources, statusIds) {
        let template_resources = [], i = 0, resource = null;
        for (i in resources) {
            resource = resources[i];
            if (statusIds.includes(resource.resource_compliance.status_id)) {
                template_resource = this.component_check_resource(resources[i]);
                template_resources.push(template_resource);
            }
        }
        return template_resources;
    },
    component_check_resource: function(resource) {
        let status = this.find_status_by_id(resource.resource_compliance.status_id);
        let template = {
            compliance: resource.resource_compliance,
            resource: resource,
            status: status
        }
        return template;
    },
    audit_status: function(data) {
        template = extend({}, data);
        template.audit.account_subscription_id = {
            account_id: data.account,
            account_name: null
        };
        template.audit.date_completed = template.audit.completed;
        template.audit.date_upated = template.audit.completed;
        let check_stats = [];
        let aliases = this.reference_aliases();
        for(i in data.audit.checks) {
            let check = data.audit.checks[i];
            let summary = this.component_check_summary(check);
            check_stats.push(summary);
        }
        for (key in aliases) {
            let alias = aliases[key]
            data.audit.summary[alias] = data.audit.summary[key];
        }

        template.audit_stats = {
            all: data.audit.summary,
            criteria: check_stats
        };
        template.breadcrumbs = [
            {
                title: "Audit list",
                link: "/../../../.."
            }
        ];
        return template;
    },
    audit_raw: function(data) {
        template = extend({}, data);
        template.breadcrumbs = [
            {
                title: "Audit list",
                link: "/../../../../../.."
            },
            {
                title: "Audit: " + this.format_date_string(data.audit_date),
                link: "/."
            }
        ];
        return template
    },
    check_status_resources: function(data) {
        template = extend({}, data);
        let statusId = (data.status_name == 'passed')?2:3;
        let statusIds = (data.status_name == 'passed')?[2,4]:[3];
        let status = this.find_status_by_id(statusId);
        let check = this.find_check_by_id(data.audit.checks, data.check_id);
        data.status = status;
        template.audit.account_subscription_id = {
            account_id: data.account,
            account_name: null
        };
        template.audit.date_completed = template.audit.completed;
        template.audit.date_upated = template.audit.completed;
        template.check = check;
        let i = 0;
        let template_resources = this.find_resources_by_status(check.resources, statusIds);
        template.resources = template_resources;
        template.breadcrumbs = [
            {
                title: "Audit list",
                link: "/../../../../../.."
            },
            {
                title: "Audit: " + this.format_date_string(data.audit_date),
                //link: "/accounts/"+data.account+"/audit/"+data.audit_date
                link: "/."
            }
        ];
        return template;
    }
}

module.exports = templater;