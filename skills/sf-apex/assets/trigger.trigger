/**
 * @description Trigger for {{ObjectName}} using Trigger Actions Framework
 * @author {{Author}}
 * @date {{Date}}
 */
trigger {{ObjectName}}Trigger on {{ObjectName}} (
    before insert,
    after insert,
    before update,
    after update,
    before delete,
    after delete,
    after undelete
) {
    new MetadataTriggerHandler().run();
}
