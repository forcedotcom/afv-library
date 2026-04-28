-- Extract interactions from Data Cloud
-- DMO: ssot__AIAgentInteraction__dlm
--
-- Usage: Replace {{SESSION_IDS}} with comma-separated session IDs
--
-- Interactions represent individual turns in the conversation.
-- Each turn starts with user input and ends with agent response.
-- SESSION_END interactions mark when the session concluded.

SELECT
    ssot__Id__c,
    ssot__AiAgentSessionId__c,
    ssot__AiAgentInteractionType__c,
    ssot__TopicApiName__c,
    ssot__StartTimestamp__c,
    ssot__EndTimestamp__c
FROM ssot__AIAgentInteraction__dlm
WHERE ssot__AiAgentSessionId__c IN ({{SESSION_IDS}})
ORDER BY ssot__StartTimestamp__c;


-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Interactions for specific session
-- SELECT * FROM ssot__AIAgentInteraction__dlm
-- WHERE ssot__AiAgentSessionId__c = 'a0x1234567890ABC';

-- Count turns per session
-- SELECT
--     ssot__AiAgentSessionId__c,
--     COUNT(*) as turn_count
-- FROM ssot__AIAgentInteraction__dlm
-- WHERE ssot__AiAgentInteractionType__c = 'TURN'
-- GROUP BY ssot__AiAgentSessionId__c;

-- Topic distribution
-- SELECT
--     ssot__TopicApiName__c,
--     COUNT(*) as count
-- FROM ssot__AIAgentInteraction__dlm
-- WHERE ssot__AiAgentInteractionType__c = 'TURN'
-- GROUP BY ssot__TopicApiName__c
-- ORDER BY count DESC;

-- Find sessions with topic switches (multiple topics)
-- SELECT
--     ssot__AiAgentSessionId__c,
--     COUNT(DISTINCT ssot__TopicApiName__c) as topic_count
-- FROM ssot__AIAgentInteraction__dlm
-- WHERE ssot__AiAgentInteractionType__c = 'TURN'
-- GROUP BY ssot__AiAgentSessionId__c
-- HAVING COUNT(DISTINCT ssot__TopicApiName__c) > 1;
