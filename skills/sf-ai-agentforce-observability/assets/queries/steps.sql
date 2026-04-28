-- Extract interaction steps from Data Cloud
-- DMO: ssot__AIAgentInteractionStep__dlm
--
-- Usage: Replace {{INTERACTION_IDS}} with comma-separated interaction IDs
--
-- Steps are the individual processing units within a turn:
-- - LLM_STEP: Language model reasoning and generation
-- - ACTION_STEP: Flow/Apex action execution
--
-- Each step includes input/output data and variable state changes.

SELECT
    ssot__Id__c,
    ssot__AiAgentInteractionId__c,
    ssot__AiAgentInteractionStepType__c,
    ssot__Name__c,
    ssot__InputValueText__c,
    ssot__OutputValueText__c,
    ssot__PreStepVariableText__c,
    ssot__PostStepVariableText__c,
    ssot__GenerationId__c
FROM ssot__AIAgentInteractionStep__dlm
WHERE ssot__AiAgentInteractionId__c IN ({{INTERACTION_IDS}});


-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Steps for specific interaction
-- SELECT * FROM ssot__AIAgentInteractionStep__dlm
-- WHERE ssot__AiAgentInteractionId__c = 'a0y1234567890ABC';

-- Action step distribution
-- SELECT
--     ssot__Name__c as action_name,
--     COUNT(*) as count
-- FROM ssot__AIAgentInteractionStep__dlm
-- WHERE ssot__AiAgentInteractionStepType__c = 'ACTION_STEP'
-- GROUP BY ssot__Name__c
-- ORDER BY count DESC;

-- LLM vs Action step ratio
-- SELECT
--     ssot__AiAgentInteractionStepType__c,
--     COUNT(*) as count
-- FROM ssot__AIAgentInteractionStep__dlm
-- GROUP BY ssot__AiAgentInteractionStepType__c;

-- Find steps with large outputs (potential issues)
-- SELECT
--     ssot__Id__c,
--     ssot__Name__c,
--     LENGTH(ssot__OutputValueText__c) as output_length
-- FROM ssot__AIAgentInteractionStep__dlm
-- WHERE LENGTH(ssot__OutputValueText__c) > 10000
-- ORDER BY output_length DESC;

-- Steps with specific action name
-- SELECT * FROM ssot__AIAgentInteractionStep__dlm
-- WHERE ssot__Name__c = 'Get_Order_Status'
--   AND ssot__AiAgentInteractionStepType__c = 'ACTION_STEP';
