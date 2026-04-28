<!-- Parent: sf-flow/SKILL.md -->
# Salesforce Flow Wait Element Patterns

Comprehensive guide to using Wait elements in Salesforce Flows for time-based and condition-based pausing.

## Flow Type Compatibility

Wait elements have **strict flow type requirements**:

| Flow Type | Wait Supported? | Notes |
|-----------|-----------------|-------|
| **Autolaunched Flow** | ✅ Yes | Primary use case |
| **Scheduled Flow** | ✅ Yes | Often combined with scheduling |
| **Orchestration** | ✅ Yes | For complex multi-step processes |
| **Screen Flow** | ❌ No | Cannot pause user sessions |
| **Record-Triggered Flow** | ❌ No | Must complete synchronously |
| **Platform Event Flow** | ❌ No | Event-driven, no waiting |

**Key Insight**: If you need wait behavior in a Record-Triggered Flow, call an Autolaunched subflow that contains the Wait element.

---

## Three Wait Element Types

### 1. Wait for Amount of Time (Duration-Based)

Pauses flow execution for a fixed duration.

**Use Cases:**
- Send follow-up email 24 hours after form submission
- Escalate case if not resolved within 48 hours
- Wait 7 days before survey request

**XML Structure:**
```xml
<waits>
    <name>Wait_7_Days</name>
    <label>Wait 7 Days</label>
    <waitEvents>
        <name>Duration_Complete</name>
        <eventType>AlarmEvent</eventType>
        <inputParameters>
            <name>AlarmTime</name>
            <value>
                <elementReference>$Flow.CurrentDateTime</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>TimeOffset</name>
            <value>
                <numberValue>7.0</numberValue>
            </value>
        </inputParameters>
        <inputParameters>
            <name>TimeOffsetUnit</name>
            <value>
                <stringValue>Days</stringValue>
            </value>
        </inputParameters>
        <connector>
            <targetReference>Next_Element</targetReference>
        </connector>
    </waitEvents>
</waits>
```

**TimeOffsetUnit Options:**
- `Minutes`
- `Hours`
- `Days`
- `Months`

---

### 2. Wait Until Date (Date-Based)

Pauses until a specific date/time is reached.

**Use Cases:**
- Resume on contract expiration date
- Notify before subscription renewal
- Trigger on scheduled meeting time

**XML Structure:**
```xml
<waits>
    <name>Wait_Until_Renewal</name>
    <label>Wait Until Renewal Date</label>
    <waitEvents>
        <name>Date_Reached</name>
        <eventType>DateRefAlarmEvent</eventType>
        <inputParameters>
            <name>DateTime</name>
            <value>
                <elementReference>var_RenewalDate</elementReference>
            </value>
        </inputParameters>
        <connector>
            <targetReference>Send_Renewal_Reminder</targetReference>
        </connector>
    </waitEvents>
</waits>
```

**Pro Tip:** Use a formula to calculate the target date:
```xml
<formulas>
    <name>formula_RenewalReminder</name>
    <dataType>DateTime</dataType>
    <!-- 30 days before renewal -->
    <expression>{!rec_Contract.EndDate} - 30</expression>
</formulas>
```

---

### 3. Wait for Conditions (Condition-Based)

Pauses until a field meets specified criteria OR timeout expires.

**Use Cases:**
- Resume when Case Status changes to 'Closed'
- Resume when Approval Status is 'Approved'
- Resume when Payment is 'Received'

**XML Structure:**
```xml
<waits>
    <name>Wait_For_Approval</name>
    <label>Wait for Approval</label>
    <defaultConnector>
        <targetReference>Handle_Timeout</targetReference>
    </defaultConnector>
    <defaultConnectorLabel>Max Wait Exceeded</defaultConnectorLabel>
    <waitEvents>
        <name>Approval_Received</name>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>rec_Request.Status__c</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue>
                <stringValue>Approved</stringValue>
            </rightValue>
        </conditions>
        <eventType>AlarmEvent</eventType>
        <inputParameters>
            <name>AlarmTime</name>
            <value>
                <elementReference>$Flow.CurrentDateTime</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>TimeOffset</name>
            <value>
                <numberValue>30.0</numberValue>
            </value>
        </inputParameters>
        <inputParameters>
            <name>TimeOffsetUnit</name>
            <value>
                <stringValue>Days</stringValue>
            </value>
        </inputParameters>
        <connector>
            <targetReference>Process_Approved_Request</targetReference>
        </connector>
        <label>Approved</label>
    </waitEvents>
</waits>
```

**Warning:** Condition-based waits are complex. Consider Platform Events for simpler event-driven patterns.

---

## Best Practices

### 1. Always Handle Timeout Paths

```xml
<waits>
    <name>Wait_With_Timeout</name>
    <defaultConnector>
        <targetReference>Handle_Timeout</targetReference>
    </defaultConnector>
    <defaultConnectorLabel>Timeout - No Response</defaultConnectorLabel>
    <!-- waitEvents... -->
</waits>
```

### 2. Consider Governor Limits

Waiting flows consume org resources:
- Each paused flow interview counts against limits
- Long waits with many instances can accumulate
- Monitor with Setup → Flows → Paused and Waiting Interviews

### 3. Use Variables for Dynamic Durations

```xml
<variables>
    <name>var_WaitDays</name>
    <dataType>Number</dataType>
    <value>
        <numberValue>7.0</numberValue>
    </value>
</variables>

<!-- Reference in Wait -->
<inputParameters>
    <name>TimeOffset</name>
    <value>
        <elementReference>var_WaitDays</elementReference>
    </value>
</inputParameters>
```

### 4. Test with Shorter Durations

In sandbox environments:
- Use minutes instead of days for testing
- Verify timeout paths work correctly
- Check debug logs for wait behavior

### 5. Document Wait Logic

Add XML comments explaining:
- Why this duration was chosen
- What happens on timeout
- Business context for the wait

```xml
<!--
    Wait 7 days for customer response.
    Business Rule: BR-2024-015 - Follow-up SLA
    Timeout Action: Escalate to manager
-->
<waits>
    <name>Wait_Customer_Response</name>
    <!-- ... -->
</waits>
```

---

## Common Patterns

### Follow-Up Email Pattern

```
Start
  ↓
Create Case → Wait 24 Hours → Check Status → (If Open) → Send Follow-Up
                                    ↓
                            (If Closed) → End
```

### Escalation Ladder Pattern

```
Start
  ↓
Create Task → Wait 2 Days → Not Complete? → Escalate to Lead
                                ↓
                    Wait 2 Days → Not Complete? → Escalate to Manager
                                        ↓
                            Wait 1 Day → Auto-Close with Note
```

### Approval Wait Pattern

```
Start
  ↓
Submit for Approval → Wait for Approval (30 day max)
                            ↓                    ↓
                     (Approved)              (Timeout)
                         ↓                       ↓
                  Process Request         Notify Submitter
```

---

## Platform Events vs. Wait for Conditions

Consider Platform Events when:

| Scenario | Use Wait | Use Platform Event |
|----------|----------|-------------------|
| Fixed time delay | ✅ | ❌ |
| Wait for date | ✅ | ❌ |
| External system callback | ❌ | ✅ |
| Real-time field change | ❌ | ✅ |
| Complex event correlation | ❌ | ✅ |
| Simple status check | ✅ | ❌ |

**Platform Event Advantage:** Immediate response when event fires, no polling delay.

**Wait Advantage:** Simpler setup, no Platform Event definition required.

---

## Troubleshooting

### Paused Interview Not Resuming

1. Check interview status in Setup → Flows → Paused and Waiting Interviews
2. Verify target date hasn't passed (for Date-based waits)
3. Check condition field values match expected criteria
4. Review debug logs for errors during resume

### Too Many Paused Interviews

1. Add timeout paths to prevent indefinite waits
2. Consider batch cleanup flow for stale interviews
3. Reduce wait durations where possible
4. Use `Database.deleteAsync()` in Apex for cleanup

### Performance Issues

1. Avoid Wait elements in high-volume flows
2. Consider Platform Events for real-time needs
3. Use Scheduled Flows instead of Wait for batch operations

---

## Related Templates

- `sf-flow/assets/wait-template.xml` - All three wait patterns with examples
- `sf-flow/assets/platform-event-flow-template.xml` - Event-driven alternative
- `sf-flow/assets/scheduled-flow-template.xml` - Scheduled batch processing
