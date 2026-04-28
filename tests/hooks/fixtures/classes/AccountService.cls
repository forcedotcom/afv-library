public with sharing class AccountService {
    public static List<Account> getActiveAccounts(Set<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) {
            return new List<Account>();
        }
        try {
            return [
                SELECT Id, Name, Industry, AnnualRevenue
                FROM Account
                WHERE Id IN :accountIds AND IsDeleted = FALSE
                LIMIT 200
            ];
        } catch (QueryException e) {
            System.debug(LoggingLevel.ERROR, 'Failed to query accounts: ' + e.getMessage());
            throw new AccountServiceException('Unable to retrieve accounts', e);
        }
    }

    public static void updateAccountStatuses(List<Account> accounts) {
        if (accounts == null || accounts.isEmpty()) {
            return;
        }
        List<Account> toUpdate = new List<Account>();
        for (Account acc : accounts) {
            if (acc.AnnualRevenue > 1000000) {
                toUpdate.add(new Account(Id = acc.Id, Rating = 'Hot'));
            }
        }
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }

    public class AccountServiceException extends Exception {
    }
}
