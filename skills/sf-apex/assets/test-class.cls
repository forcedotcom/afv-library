/**
 * @description Test class for {{TestedClassName}}
 * @author {{Author}}
 * @date {{Date}}
 */
@isTest
private class {{TestedClassName}}Test {

    @TestSetup
    static void setup() {
        // Create test data using TestDataFactory
        // TestDataFactory.createAccounts(5);
    }

    @isTest
    static void testPositiveScenario() {
        // Arrange
        // Query test data or create specific records

        // Act
        Test.startTest();
        // Call method under test
        Test.stopTest();

        // Assert
        // Assert.areEqual(expected, actual, 'Message');
    }

    @isTest
    static void testNegativeScenario() {
        // Arrange - setup invalid data

        // Act & Assert
        Test.startTest();
        try {
            // Call method that should throw exception
            Assert.fail('Expected exception was not thrown');
        } catch ({{ExceptionType}} e) {
            Assert.isTrue(e.getMessage().contains('expected text'), 'Error message should contain expected text');
        }
        Test.stopTest();
    }

    @isTest
    static void testBulkScenario() {
        // Arrange - create 251+ records to span trigger batches
        List<{{ObjectName}}> records = new List<{{ObjectName}}>();
        for (Integer i = 0; i < 251; i++) {
            records.add(new {{ObjectName}}(
                Name = 'Test ' + i
            ));
        }

        // Act
        Test.startTest();
        insert records;
        Test.stopTest();

        // Assert
        Assert.areEqual(251, [SELECT COUNT() FROM {{ObjectName}}], 'All records should be created');
    }

    @isTest
    static void testNullInput() {
        // Test null handling
        Test.startTest();
        try {
            // Call method with null
            Assert.fail('Expected exception for null input');
        } catch (IllegalArgumentException e) {
            Assert.isTrue(e.getMessage().contains('null'), 'Should mention null');
        }
        Test.stopTest();
    }
}
