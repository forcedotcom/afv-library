-- Extract messages from Data Cloud
-- DMO: ssot__AIAgentMoment__dlm
--
-- Usage: Replace {{INTERACTION_IDS}} with comma-separated interaction IDs
--
-- Messages are the actual conversation content:
-- - INPUT: User messages
-- - OUTPUT: Agent responses
--
-- Used for reconstructing conversation timelines for debugging.

SELECT
    ssot__Id__c,
    ssot__AiAgentInteractionId__c,
    ssot__ContentText__c,
    ssot__AiAgentInteractionMessageType__c,
    ssot__MessageSentTimestamp__c
FROM ssot__AIAgentMoment__dlm
WHERE ssot__AiAgentInteractionId__c IN ({{INTERACTION_IDS}})
ORDER BY ssot__MessageSentTimestamp__c;


-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Messages for specific interaction
-- SELECT * FROM ssot__AIAgentMoment__dlm
-- WHERE ssot__AiAgentInteractionId__c = 'a0y1234567890ABC'
-- ORDER BY ssot__MessageSentTimestamp__c;

-- Message type distribution
-- SELECT
--     ssot__AiAgentInteractionMessageType__c,
--     COUNT(*) as count
-- FROM ssot__AIAgentMoment__dlm
-- GROUP BY ssot__AiAgentInteractionMessageType__c;

-- Find long user messages (potential complex requests)
-- SELECT
--     ssot__Id__c,
--     ssot__ContentText__c,
--     LENGTH(ssot__ContentText__c) as length
-- FROM ssot__AIAgentMoment__dlm
-- WHERE ssot__AiAgentInteractionMessageType__c = 'INPUT'
--   AND LENGTH(ssot__ContentText__c) > 500
-- ORDER BY length DESC;

-- Search messages for specific keyword
-- SELECT * FROM ssot__AIAgentMoment__dlm
-- WHERE ssot__ContentText__c LIKE '%order%'
--   AND ssot__AiAgentInteractionMessageType__c = 'INPUT';

-- Average message length by type
-- SELECT
--     ssot__AiAgentInteractionMessageType__c,
--     AVG(LENGTH(ssot__ContentText__c)) as avg_length
-- FROM ssot__AIAgentMoment__dlm
-- GROUP BY ssot__AiAgentInteractionMessageType__c;
