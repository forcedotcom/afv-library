/**
 * @description Factory class for creating test data
 * @author {{Author}}
 * @date {{Date}}
 */
@isTest
public class TestDataFactory {

    /**
     * @description Creates Account records
     * @param count Number of records to create
     * @return List of inserted Account records
     */
    public static List<Account> createAccounts(Integer count) {
        return createAccounts(count, true);
    }

    /**
     * @description Creates Account records with insert option
     * @param count Number of records to create
     * @param doInsert Whether to insert records
     * @return List of Account records
     */
    public static List<Account> createAccounts(Integer count, Boolean doInsert) {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < count; i++) {
            accounts.add(new Account(
                Name = 'Test Account ' + i,
                Industry = 'Technology',
                BillingCity = 'San Francisco',
                BillingState = 'CA',
                BillingCountry = 'USA'
            ));
        }
        if (doInsert) {
            insert accounts;
        }
        return accounts;
    }

    /**
     * @description Creates Contact records for an Account
     * @param count Number of records to create
     * @param accountId Parent Account Id
     * @return List of inserted Contact records
     */
    public static List<Contact> createContacts(Integer count, Id accountId) {
        List<Contact> contacts = new List<Contact>();
        for (Integer i = 0; i < count; i++) {
            contacts.add(new Contact(
                FirstName = 'Test',
                LastName = 'Contact ' + i,
                Email = 'test' + i + '@example.com',
                AccountId = accountId
            ));
        }
        insert contacts;
        return contacts;
    }

    /**
     * @description Creates Opportunity records for an Account
     * @param count Number of records to create
     * @param accountId Parent Account Id
     * @return List of inserted Opportunity records
     */
    public static List<Opportunity> createOpportunities(Integer count, Id accountId) {
        List<Opportunity> opps = new List<Opportunity>();
        for (Integer i = 0; i < count; i++) {
            opps.add(new Opportunity(
                Name = 'Test Opportunity ' + i,
                AccountId = accountId,
                StageName = 'Prospecting',
                CloseDate = Date.today().addDays(30),
                Amount = 10000 + (i * 1000)
            ));
        }
        insert opps;
        return opps;
    }

    /**
     * @description Creates a User with specified profile
     * @param profileName Name of the profile
     * @return Inserted User record
     */
    public static User createUser(String profileName) {
        Profile p = [SELECT Id FROM Profile WHERE Name = :profileName LIMIT 1];
        String uniqueKey = String.valueOf(DateTime.now().getTime());

        User u = new User(
            Alias = 'test' + uniqueKey.right(4),
            Email = 'testuser' + uniqueKey + '@example.com',
            EmailEncodingKey = 'UTF-8',
            FirstName = 'Test',
            LastName = 'User ' + uniqueKey.right(4),
            LanguageLocaleKey = 'en_US',
            LocaleSidKey = 'en_US',
            ProfileId = p.Id,
            TimeZoneSidKey = 'America/Los_Angeles',
            Username = 'testuser' + uniqueKey + '@example.com.test'
        );
        insert u;
        return u;
    }
}
