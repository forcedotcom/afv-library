/**
 * @description Selector class for {{ObjectName}} queries
 * @author {{Author}}
 * @date {{Date}}
 */
public inherited sharing class {{ObjectName}}Selector {

    /**
     * @description Default fields to query
     */
    private static final List<String> DEFAULT_FIELDS = new List<String>{
        'Id',
        'Name',
        'CreatedDate',
        'LastModifiedDate'
    };

    /**
     * @description Selects records by IDs
     * @param ids Set of record IDs
     * @return List of {{ObjectName}} records
     */
    public List<{{ObjectName}}> selectById(Set<Id> ids) {
        if (ids == null || ids.isEmpty()) {
            return new List<{{ObjectName}}>();
        }

        return [
            SELECT Id, Name, CreatedDate, LastModifiedDate
            FROM {{ObjectName}}
            WHERE Id IN :ids
            WITH USER_MODE
        ];
    }

    /**
     * @description Selects records by IDs with related records
     * @param ids Set of record IDs
     * @return List of {{ObjectName}} records with child records
     */
    public List<{{ObjectName}}> selectByIdWithRelated(Set<Id> ids) {
        if (ids == null || ids.isEmpty()) {
            return new List<{{ObjectName}}>();
        }

        return [
            SELECT Id, Name, CreatedDate, LastModifiedDate,
                (SELECT Id, Name FROM {{ChildRelationship}})
            FROM {{ObjectName}}
            WHERE Id IN :ids
            WITH USER_MODE
        ];
    }

    /**
     * @description Selects records by Name
     * @param name Name to search for (supports wildcards)
     * @return List of matching {{ObjectName}} records
     */
    public List<{{ObjectName}}> selectByName(String name) {
        if (String.isBlank(name)) {
            return new List<{{ObjectName}}>();
        }

        String searchName = '%' + String.escapeSingleQuotes(name) + '%';
        return [
            SELECT Id, Name, CreatedDate, LastModifiedDate
            FROM {{ObjectName}}
            WHERE Name LIKE :searchName
            WITH USER_MODE
            LIMIT 100
        ];
    }

    /**
     * @description Selects active records
     * @return List of active {{ObjectName}} records
     */
    public List<{{ObjectName}}> selectActive() {
        return [
            SELECT Id, Name, CreatedDate, LastModifiedDate
            FROM {{ObjectName}}
            WHERE IsActive__c = true
            WITH USER_MODE
            ORDER BY Name
        ];
    }

    /**
     * @description Selects records created in date range
     * @param startDate Start date
     * @param endDate End date
     * @return List of {{ObjectName}} records in date range
     */
    public List<{{ObjectName}}> selectByCreatedDateRange(Date startDate, Date endDate) {
        return [
            SELECT Id, Name, CreatedDate, LastModifiedDate
            FROM {{ObjectName}}
            WHERE CreatedDate >= :startDate
            AND CreatedDate <= :endDate
            WITH USER_MODE
            ORDER BY CreatedDate DESC
        ];
    }

    /**
     * @description Counts records matching criteria
     * @return Count of matching records
     */
    public Integer countAll() {
        return [SELECT COUNT() FROM {{ObjectName}} WITH USER_MODE];
    }
}
