<!-- Parent: sf-ai-agentforce/SKILL.md -->
<!-- TIER: 3 | DETAILED REFERENCE -->
<!-- Read after: SKILL.md -->
<!-- Purpose: Native AI API (aiplatform.ModelsAPI) patterns for Apex -->

# Agentforce Models API

> Native AI generation in Apex using `aiplatform.ModelsAPI` namespace

## Overview

The **Agentforce Models API** enables native LLM access directly from Apex code without external HTTP callouts. This API is part of the `aiplatform` namespace and provides access to Salesforce-managed AI models.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MODELS API ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Your Apex Code                                                             │
│       │                                                                     │
│       ▼                                                                     │
│  aiplatform.ModelsAPI.createGenerations()                                   │
│       │                                                                     │
│       ▼                                                                     │
│  Salesforce AI Gateway                                                      │
│       │                                                                     │
│       ▼                                                                     │
│  Foundation Model (GPT-4o Mini, etc.)                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### API Version Requirement

**Minimum API v61.0+ (Spring '24)** for Models API support.

```bash
# Verify org API version
sf org display --target-org [alias] --json | jq '.result.apiVersion'
```

### Einstein Generative AI Setup

1. **Einstein Generative AI** must be enabled in Setup
2. User must have **Einstein Generative AI User** permission set
3. Organization must have Einstein AI entitlement

```
Setup → Einstein Setup → Turn on Einstein
Setup → Permission Sets → Einstein Generative AI User → Assign to users
```

---

## Available Models

| Model Name | Description | Use Case |
|------------|-------------|----------|
| `sfdc_ai__DefaultOpenAIGPT4OmniMini` | GPT-4o Mini | Cost-effective general tasks |
| `sfdc_ai__DefaultOpenAIGPT4Omni` | GPT-4o | Complex reasoning tasks |
| `sfdc_ai__DefaultAnthropic` | Claude (Anthropic) | Nuanced understanding |
| `sfdc_ai__DefaultGoogleGemini` | Google Gemini | Multimodal tasks |

> **Note**: Available models depend on your Salesforce edition and Einstein entitlements.

---

## Basic Usage

### Simple Text Generation

```apex
public class ModelsApiExample {

    public static String generateText(String prompt) {
        // Create the request
        aiplatform.ModelsAPI.createGenerations_Request request =
            new aiplatform.ModelsAPI.createGenerations_Request();

        // Set the model
        request.modelName = 'sfdc_ai__DefaultOpenAIGPT4OmniMini';

        // Create the generation input
        aiplatform.ModelsAPI_GenerationRequest genRequest =
            new aiplatform.ModelsAPI_GenerationRequest();
        genRequest.prompt = prompt;

        request.body = genRequest;

        // Call the API
        aiplatform.ModelsAPI.createGenerations_Response response =
            aiplatform.ModelsAPI.createGenerations(request);

        // Extract the generated text
        if (response.Code200 != null &&
            response.Code200.generations != null &&
            !response.Code200.generations.isEmpty()) {
            return response.Code200.generations[0].text;
        }

        return null;
    }
}
```

---

## Queueable Integration

Use Queueable for async AI processing with record context:

### ❌ BAD: Synchronous AI Calls in Triggers

```apex
// DON'T DO THIS - blocks transaction, hits limits
trigger CaseTrigger on Case (after insert) {
    for (Case c : Trigger.new) {
        String summary = ModelsApiExample.generateText(c.Description);
        // This will fail or timeout
    }
}
```

### ✅ GOOD: Queueable for Async AI Processing

```apex
/**
 * @description Queueable job for generating AI summaries
 * @implements Database.AllowsCallouts - Required for API calls
 */
public with sharing class CaseSummaryQueueable implements Queueable, Database.AllowsCallouts {

    private List<Id> caseIds;

    public CaseSummaryQueueable(List<Id> caseIds) {
        this.caseIds = caseIds;
    }

    public void execute(QueueableContext context) {
        // Query cases
        List<Case> cases = [
            SELECT Id, Subject, Description
            FROM Case
            WHERE Id IN :caseIds
            WITH USER_MODE
        ];

        List<Case> toUpdate = new List<Case>();

        for (Case c : cases) {
            try {
                // Generate summary using Models API
                String summary = generateCaseSummary(c);

                if (String.isNotBlank(summary)) {
                    c.AI_Summary__c = summary;
                    toUpdate.add(c);
                }
            } catch (Exception e) {
                System.debug(LoggingLevel.ERROR,
                    'AI Summary Error for Case ' + c.Id + ': ' + e.getMessage());
            }
        }

        // Update records
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }

    private String generateCaseSummary(Case c) {
        String prompt = 'Summarize this customer support case in 2-3 sentences:\n\n' +
            'Subject: ' + c.Subject + '\n' +
            'Description: ' + c.Description;

        aiplatform.ModelsAPI.createGenerations_Request request =
            new aiplatform.ModelsAPI.createGenerations_Request();
        request.modelName = 'sfdc_ai__DefaultOpenAIGPT4OmniMini';

        aiplatform.ModelsAPI_GenerationRequest genRequest =
            new aiplatform.ModelsAPI_GenerationRequest();
        genRequest.prompt = prompt;
        request.body = genRequest;

        aiplatform.ModelsAPI.createGenerations_Response response =
            aiplatform.ModelsAPI.createGenerations(request);

        if (response.Code200 != null &&
            response.Code200.generations != null &&
            !response.Code200.generations.isEmpty()) {
            return response.Code200.generations[0].text;
        }

        return null;
    }
}
```

### Invoking from Trigger

```apex
trigger CaseTrigger on Case (after insert) {
    List<Id> newCaseIds = new List<Id>();

    for (Case c : Trigger.new) {
        if (String.isNotBlank(c.Description)) {
            newCaseIds.add(c.Id);
        }
    }

    if (!newCaseIds.isEmpty()) {
        // Enqueue async processing - non-blocking
        System.enqueueJob(new CaseSummaryQueueable(newCaseIds));
    }
}
```

---

## Batch Class Integration

For bulk AI processing, use Batch Apex:

```apex
/**
 * @description Batch job for generating AI content on records
 * @implements Database.AllowsCallouts, Database.Stateful
 */
public with sharing class OpportunitySummaryBatch
    implements Database.Batchable<sObject>, Database.AllowsCallouts, Database.Stateful {

    // Track statistics across batches
    private Integer successCount = 0;
    private Integer errorCount = 0;

    public Database.QueryLocator start(Database.BatchableContext bc) {
        // Query records needing AI summary
        return Database.getQueryLocator([
            SELECT Id, Name, Description, StageName, Amount
            FROM Opportunity
            WHERE AI_Summary__c = null
            AND Description != null
            ORDER BY CreatedDate DESC
        ]);
    }

    public void execute(Database.BatchableContext bc, List<Opportunity> scope) {
        List<Opportunity> toUpdate = new List<Opportunity>();

        for (Opportunity opp : scope) {
            try {
                String summary = generateOpportunitySummary(opp);

                if (String.isNotBlank(summary)) {
                    opp.AI_Summary__c = summary;
                    toUpdate.add(opp);
                    successCount++;
                }
            } catch (Exception e) {
                errorCount++;
                System.debug(LoggingLevel.ERROR,
                    'AI Summary Error for Opp ' + opp.Id + ': ' + e.getMessage());
            }
        }

        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }

    public void finish(Database.BatchableContext bc) {
        System.debug('Batch Complete. Success: ' + successCount + ', Errors: ' + errorCount);

        // Optional: Send completion notification
        // Messaging.SingleEmailMessage email = ...
    }

    private String generateOpportunitySummary(Opportunity opp) {
        String prompt = 'Create a brief sales summary for this opportunity:\n\n' +
            'Name: ' + opp.Name + '\n' +
            'Stage: ' + opp.StageName + '\n' +
            'Amount: $' + opp.Amount + '\n' +
            'Description: ' + opp.Description + '\n\n' +
            'Summarize in 2-3 sentences focusing on key points.';

        // Use same API pattern as Queueable
        aiplatform.ModelsAPI.createGenerations_Request request =
            new aiplatform.ModelsAPI.createGenerations_Request();
        request.modelName = 'sfdc_ai__DefaultOpenAIGPT4OmniMini';

        aiplatform.ModelsAPI_GenerationRequest genRequest =
            new aiplatform.ModelsAPI_GenerationRequest();
        genRequest.prompt = prompt;
        request.body = genRequest;

        aiplatform.ModelsAPI.createGenerations_Response response =
            aiplatform.ModelsAPI.createGenerations(request);

        if (response.Code200 != null &&
            response.Code200.generations != null &&
            !response.Code200.generations.isEmpty()) {
            return response.Code200.generations[0].text;
        }

        return null;
    }
}
```

### Batch Size Considerations

| Batch Size | AI Calls/Batch | Recommended For |
|------------|----------------|-----------------|
| 1-5 | 1-5 | Complex prompts, detailed output |
| 10-20 | 10-20 | Standard summaries |
| 50+ | Avoid | Risk of timeout, use smaller batches |

```apex
// Execute with smaller batch size for AI processing
Database.executeBatch(new OpportunitySummaryBatch(), 10);
```

---

## Chatter Integration

Post AI-generated content to Chatter:

```apex
public with sharing class ChatterAIService {

    /**
     * @description Generate and post AI insight to Chatter
     * @param recordId The record to analyze
     * @param feedMessage Additional context for the post
     */
    public static void postAIInsight(Id recordId, String feedMessage) {
        // Query record context
        Account acc = [
            SELECT Name, Industry, AnnualRevenue, Description
            FROM Account
            WHERE Id = :recordId
            LIMIT 1
        ];

        // Generate insight using Models API
        String prompt = 'Analyze this account and provide 3 key business insights:\n\n' +
            'Company: ' + acc.Name + '\n' +
            'Industry: ' + acc.Industry + '\n' +
            'Revenue: $' + acc.AnnualRevenue + '\n' +
            'Description: ' + acc.Description + '\n\n' +
            'Format as numbered bullet points.';

        String insight = generateText(prompt);

        if (String.isNotBlank(insight)) {
            // Create Chatter post
            ConnectApi.FeedItemInput feedInput = new ConnectApi.FeedItemInput();
            ConnectApi.MessageBodyInput messageInput = new ConnectApi.MessageBodyInput();
            ConnectApi.TextSegmentInput textSegment = new ConnectApi.TextSegmentInput();

            textSegment.text = '🤖 AI Account Insight:\n\n' + insight;
            messageInput.messageSegments = new List<ConnectApi.MessageSegmentInput>{ textSegment };
            feedInput.body = messageInput;
            feedInput.feedElementType = ConnectApi.FeedElementType.FeedItem;
            feedInput.subjectId = recordId;

            ConnectApi.ChatterFeeds.postFeedElement(
                Network.getNetworkId(),
                feedInput
            );
        }
    }

    private static String generateText(String prompt) {
        aiplatform.ModelsAPI.createGenerations_Request request =
            new aiplatform.ModelsAPI.createGenerations_Request();
        request.modelName = 'sfdc_ai__DefaultOpenAIGPT4OmniMini';

        aiplatform.ModelsAPI_GenerationRequest genRequest =
            new aiplatform.ModelsAPI_GenerationRequest();
        genRequest.prompt = prompt;
        request.body = genRequest;

        aiplatform.ModelsAPI.createGenerations_Response response =
            aiplatform.ModelsAPI.createGenerations(request);

        if (response.Code200 != null &&
            response.Code200.generations != null &&
            !response.Code200.generations.isEmpty()) {
            return response.Code200.generations[0].text;
        }

        return null;
    }
}
```

---

## Governor Limits & Best Practices

### Limits to Consider

| Limit | Value | Mitigation |
|-------|-------|------------|
| Callout time | 120s total | Use smaller batches, Queueable chaining |
| Callouts per transaction | 100 | Batch records, use async |
| CPU time | 10s sync, 60s async | Use Queueable/Batch |
| Heap size | 6MB sync, 12MB async | Limit prompt/response size |

### Best Practices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MODELS API BEST PRACTICES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ARCHITECTURE                                                               │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ✅ Use Queueable for single-record async processing                        │
│  ✅ Use Batch for bulk processing (scope size 10-20)                        │
│  ✅ Use Platform Events for notification when AI completes                  │
│  ✅ Cache common AI responses if possible                                   │
│  ❌ Don't call Models API synchronously in triggers                         │
│  ❌ Don't process unbounded record sets                                     │
│                                                                             │
│  PROMPTS                                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ✅ Be specific about expected output format                                │
│  ✅ Set length constraints ("summarize in 2 sentences")                     │
│  ✅ Include context needed for accurate responses                           │
│  ❌ Don't include PII in prompts unless necessary                           │
│  ❌ Don't rely on AI for compliance-critical decisions                      │
│                                                                             │
│  ERROR HANDLING                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ✅ Wrap API calls in try-catch                                             │
│  ✅ Log errors with context for debugging                                   │
│  ✅ Implement retry logic for transient failures                            │
│  ✅ Check response.Code200 before accessing results                         │
│  ❌ Don't assume AI responses are always successful                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Common Patterns

### Pattern 1: Service Layer Abstraction

```apex
public with sharing class AIGenerationService {

    private static final String DEFAULT_MODEL = 'sfdc_ai__DefaultOpenAIGPT4OmniMini';

    /**
     * @description Generate text with standard configuration
     */
    public static String generate(String prompt) {
        return generate(prompt, DEFAULT_MODEL);
    }

    /**
     * @description Generate text with specific model
     */
    public static String generate(String prompt, String modelName) {
        try {
            aiplatform.ModelsAPI.createGenerations_Request request =
                new aiplatform.ModelsAPI.createGenerations_Request();
            request.modelName = modelName;

            aiplatform.ModelsAPI_GenerationRequest genRequest =
                new aiplatform.ModelsAPI_GenerationRequest();
            genRequest.prompt = prompt;
            request.body = genRequest;

            aiplatform.ModelsAPI.createGenerations_Response response =
                aiplatform.ModelsAPI.createGenerations(request);

            if (response.Code200 != null &&
                response.Code200.generations != null &&
                !response.Code200.generations.isEmpty()) {
                return response.Code200.generations[0].text;
            }
        } catch (Exception e) {
            System.debug(LoggingLevel.ERROR, 'AI Generation Error: ' + e.getMessage());
        }

        return null;
    }
}
```

### Pattern 2: Notify Completion via Platform Events

```apex
// Platform Event: AI_Generation_Complete__e
// Fields: Record_Id__c (Text), Status__c (Text), Summary__c (Long Text)

public with sharing class AIQueueableWithNotification
    implements Queueable, Database.AllowsCallouts {

    private Id recordId;

    public AIQueueableWithNotification(Id recordId) {
        this.recordId = recordId;
    }

    public void execute(QueueableContext context) {
        String summary;
        String status = 'Success';

        try {
            // Generate AI content
            summary = AIGenerationService.generate('...');
        } catch (Exception e) {
            status = 'Error: ' + e.getMessage();
        }

        // Publish completion event
        AI_Generation_Complete__e event = new AI_Generation_Complete__e();
        event.Record_Id__c = recordId;
        event.Status__c = status;
        event.Summary__c = summary;

        EventBus.publish(event);
    }
}
```

### Pattern 3: LWC Subscribes to Completion

```javascript
// In your LWC controller
import { subscribe, unsubscribe, onError } from 'lightning/empApi';

connectedCallback() {
    this.subscribeToAICompletion();
}

subscribeToAICompletion() {
    const channelName = '/event/AI_Generation_Complete__e';

    subscribe(channelName, -1, (message) => {
        const payload = message.data.payload;

        if (payload.Record_Id__c === this.recordId) {
            this.aiSummary = payload.Summary__c;
            this.isLoading = false;
        }
    }).then((response) => {
        this.subscription = response;
    });
}
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Model not found" | Invalid model name | Use exact name: `sfdc_ai__DefaultOpenAIGPT4OmniMini` |
| "Access denied" | Missing permission | Assign Einstein Generative AI User permission set |
| "Callout not allowed" | Sync context restriction | Use Queueable with `Database.AllowsCallouts` |
| Timeout errors | Large prompt/response | Reduce prompt size, use batch with smaller scope |
| Empty response | Null check failed | Always validate `response.Code200` and `generations` |

---

## Related Documentation

- [Prompt Templates](prompt-templates.md) - Using AI via metadata
- [Salesforce AI Documentation](https://developer.salesforce.com/docs/einstein/genai/overview)

---

## Source

> **Reference**: [Agentforce API Generating Case Summaries with Apex Queueable](https://salesforcediaries.com/2025/07/15/agentforce-api-generating-case-summaries-with-apex-queueable/) - Salesforce Diaries
