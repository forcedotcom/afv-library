/**
 * @description Trigger action for {{ObjectName}}: {{ActionDescription}}
 * @author {{Author}}
 * @date {{Date}}
 */
public with sharing class TA_{{ObjectName}}_{{ActionName}} implements TriggerAction.{{TriggerContext}} {

    /**
     * @description {{ContextDescription}}
     * @param newList List of {{ObjectName}} records being processed
     */
    public void {{contextMethod}}(List<{{ObjectName}}> newList) {
        for ({{ObjectName}} record : newList) {
            // TODO: Implement logic
        }
    }
}

// For BeforeUpdate/AfterUpdate contexts, use this signature:
// public void {{contextMethod}}(List<{{ObjectName}}> newList, List<{{ObjectName}}> oldList) {
//     Map<Id, {{ObjectName}}> oldMap = new Map<Id, {{ObjectName}}>(oldList);
//     for ({{ObjectName}} record : newList) {
//         {{ObjectName}} oldRecord = oldMap.get(record.Id);
//         // Compare old vs new values
//     }
// }
