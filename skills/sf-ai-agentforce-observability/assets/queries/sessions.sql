-- Extract sessions from Data Cloud
-- DMO: ssot__AIAgentSession__dlm
--
-- Usage: Replace {{START_DATE}}, {{END_DATE}}
--
-- This query extracts session-level data including:
-- - Session ID and timestamps
-- - Channel type (how user connected)
-- - How the session ended (Completed, Abandoned, Escalated, etc.)
-- - Related messaging session (if applicable)
--
-- NOTE: Agent name is NOT on Session table. Join with Moment to get agent info.

SELECT
    ssot__Id__c,
    ssot__AiAgentChannelType__c,
    ssot__StartTimestamp__c,
    ssot__EndTimestamp__c,
    ssot__AiAgentSessionEndType__c,
    ssot__RelatedMessagingSessionId__c,
    ssot__InternalOrganizationId__c
FROM ssot__AIAgentSession__dlm
WHERE ssot__StartTimestamp__c >= '{{START_DATE}}'
  AND ssot__StartTimestamp__c < '{{END_DATE}}'
ORDER BY ssot__StartTimestamp__c;


-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Last 7 days of sessions
-- SELECT * FROM ssot__AIAgentSession__dlm
-- WHERE ssot__StartTimestamp__c >= '2026-01-21T00:00:00.000Z'
-- ORDER BY ssot__StartTimestamp__c;

-- Sessions by agent (requires Moment join)
-- SELECT DISTINCT s.*
-- FROM ssot__AIAgentSession__dlm s
-- JOIN ssot__AiAgentMoment__dlm m
--     ON m.ssot__AiAgentSessionId__c = s.ssot__Id__c
-- WHERE m.ssot__AiAgentApiName__c = 'Customer_Support_Agent'
--   AND s.ssot__StartTimestamp__c >= '2026-01-01T00:00:00.000Z';

-- Failed/escalated sessions only
-- SELECT * FROM ssot__AIAgentSession__dlm
-- WHERE ssot__AiAgentSessionEndType__c IN ('Escalated', 'Abandoned', 'Failed')
--   AND ssot__StartTimestamp__c >= '2026-01-01T00:00:00.000Z';

-- Session count by end type
-- SELECT
--     ssot__AiAgentSessionEndType__c,
--     COUNT(*) as session_count
-- FROM ssot__AIAgentSession__dlm
-- WHERE ssot__StartTimestamp__c >= '2026-01-01T00:00:00.000Z'
-- GROUP BY ssot__AiAgentSessionEndType__c;
