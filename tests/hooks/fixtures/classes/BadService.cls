public class BadService {
    public static void processAccounts() {
        List<Account> accounts = [SELECT Id, Name FROM Account];
        for (Account acc : accounts) {
            List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
            acc.Description = 'Contacts: ' + contacts.size();
            update acc;
        }
    }

    public static ArrayList<String> getNames() {
        ArrayList<String> names = new ArrayList<String>();
        return names;
    }

    public static void logSensitiveData(String password) {
        System.debug('Password is: ' + password);
    }
}
