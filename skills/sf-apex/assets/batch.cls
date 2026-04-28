/**
 * @description Batch job for {{Description}}
 * @author {{Author}}
 * @date {{Date}}
 */
public with sharing class {{ClassName}}_Batch implements Database.Batchable<SObject>, Database.Stateful {

    private Integer recordsProcessed = 0;
    private Integer recordsFailed = 0;
    private List<String> errors = new List<String>();

    /**
     * @description Start method - defines the scope of records to process
     * @param bc BatchableContext
     * @return QueryLocator for the records to process
     */
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id, Name
            FROM {{ObjectName}}
            WHERE Status__c = 'Pending'
            WITH USER_MODE
        ]);
    }

    /**
     * @description Execute method - processes each batch of records
     * @param bc BatchableContext
     * @param scope List of records in current batch
     */
    public void execute(Database.BatchableContext bc, List<{{ObjectName}}> scope) {
        List<{{ObjectName}}> toUpdate = new List<{{ObjectName}}>();

        for ({{ObjectName}} record : scope) {
            try {
                // TODO: Implement processing logic
                record.Status__c = 'Processed';
                toUpdate.add(record);
                recordsProcessed++;
            } catch (Exception e) {
                recordsFailed++;
                errors.add('Record ' + record.Id + ': ' + e.getMessage());
            }
        }

        if (!toUpdate.isEmpty()) {
            Database.SaveResult[] results = Database.update(toUpdate, false);
            for (Integer i = 0; i < results.size(); i++) {
                if (!results[i].isSuccess()) {
                    recordsFailed++;
                    for (Database.Error err : results[i].getErrors()) {
                        errors.add('Record ' + toUpdate[i].Id + ': ' + err.getMessage());
                    }
                }
            }
        }
    }

    /**
     * @description Finish method - called after all batches complete
     * @param bc BatchableContext
     */
    public void finish(Database.BatchableContext bc) {
        // Log results
        System.debug('{{ClassName}}_Batch completed:');
        System.debug('Records processed: ' + recordsProcessed);
        System.debug('Records failed: ' + recordsFailed);

        if (!errors.isEmpty()) {
            System.debug('Errors:');
            for (String error : errors) {
                System.debug(error);
            }
        }

        // Optional: Send completion email
        // sendCompletionEmail(bc.getJobId());

        // Optional: Chain next batch
        // Database.executeBatch(new NextBatch());
    }

    /**
     * @description Sends completion notification email
     * @param jobId The batch job ID
     */
    @SuppressWarnings('PMD.ApexSOQLInjection')
    private void sendCompletionEmail(Id jobId) {
        AsyncApexJob job = [
            SELECT Id, Status, NumberOfErrors, JobItemsProcessed, TotalJobItems
            FROM AsyncApexJob
            WHERE Id = :jobId
        ];

        Messaging.SingleEmailMessage email = new Messaging.SingleEmailMessage();
        email.setToAddresses(new List<String>{UserInfo.getUserEmail()});
        email.setSubject('{{ClassName}}_Batch Completed: ' + job.Status);
        email.setPlainTextBody(
            'Job ID: ' + jobId + '\n' +
            'Status: ' + job.Status + '\n' +
            'Items Processed: ' + job.JobItemsProcessed + '/' + job.TotalJobItems + '\n' +
            'Errors: ' + job.NumberOfErrors
        );
        Messaging.sendEmail(new List<Messaging.Email>{email});
    }
}

// Usage:
// Database.executeBatch(new {{ClassName}}_Batch(), 200);
// Or schedule:
// System.schedule('{{ClassName}} Daily', '0 0 1 * * ?', new {{ClassName}}_Scheduler());
