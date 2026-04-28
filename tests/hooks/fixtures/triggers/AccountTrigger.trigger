trigger AccountTrigger on Account(before insert, before update) {
    if (Trigger.isBefore) {
        if (Trigger.isInsert || Trigger.isUpdate) {
            AccountTriggerHandler.handleBeforeInsertUpdate(Trigger.new);
        }
    }
}
