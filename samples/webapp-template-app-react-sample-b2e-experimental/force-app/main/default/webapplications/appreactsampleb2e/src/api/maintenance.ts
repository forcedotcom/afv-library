import { getDataSDK } from "@salesforce/sdk-data";
import type { MaintenanceRequest } from "../lib/types.js";
import { gql } from "./utils.js";
import type {
	GetMaintenanceRequestsQuery,
	GetMaintenanceRequestsQueryVariables,
	GetAllMaintenanceRequestsQuery,
	GetAllMaintenanceRequestsQueryVariables,
} from "./graphql-operations-types.js";

// Query to get recent maintenance requests
const GET_MAINTENANCE_REQUESTS = gql`
	query GetMaintenanceRequests($first: Int) {
		uiapi {
			query {
				Maintenance_Request__c(first: $first, orderBy: { Priority__c: { order: DESC } }) {
					edges {
						node {
							Id
							Name {
								value
							}
							Property__r {
								Address__c {
									value
								}
							}
							User__r {
								Name {
									value
								}
							}
							Type__c {
								value
							}
							Priority__c {
								value
							}
							Status__c {
								value
							}
							Description__c {
								value
							}
							Scheduled__c {
								value
							}
						}
					}
				}
			}
		}
	}
`;

// Query to get all maintenance requests for the maintenance page
const GET_ALL_MAINTENANCE_REQUESTS = gql`
	query GetAllMaintenanceRequests($first: Int, $after: String) {
		uiapi {
			query {
				Maintenance_Request__c(
					first: $first
					after: $after
					orderBy: { Priority__c: { order: DESC }, Scheduled__c: { order: ASC } }
				) {
					edges {
						node {
							Id
							Name {
								value
							}
							Description__c {
								value
							}
							Type__c {
								value
							}
							Priority__c {
								value
							}
							Status__c {
								value
							}
							Scheduled__c {
								value
							}
							Property__r {
								Address__c {
									value
								}
								Name {
									value
								}
							}
							User__r {
								Name {
									value
								}
							}
							Owner {
								... on User {
									Name {
										value
									}
								}
							}
							ContentDocumentLinks(first: 1) {
								edges {
									node {
										ContentDocument {
											LatestPublishedVersionId {
												value
											}
										}
									}
								}
							}
						}
					}
					pageInfo {
						hasNextPage
						endCursor
					}
				}
			}
		}
	}
`;

// Fetch maintenance requests for dashboard
export async function getMaintenanceRequests(first: number = 5): Promise<MaintenanceRequest[]> {
	const variables: GetMaintenanceRequestsQueryVariables = { first };
	const data = await getDataSDK();
	const result = await data.graphql?.<
		GetMaintenanceRequestsQuery,
		GetMaintenanceRequestsQueryVariables
	>(GET_MAINTENANCE_REQUESTS, variables);

	if (result?.errors?.length) {
		const errorMessages = result.errors.map((e) => e.message).join("; ");
		throw new Error(`GraphQL Error: ${errorMessages}`);
	}

	const requests =
		result?.data?.uiapi?.query?.Maintenance_Request__c?.edges?.map((edge) =>
			transformMaintenanceRequest(edge?.node),
		) || [];
	return requests;
}

// Fetch all maintenance requests for the maintenance page
export async function getAllMaintenanceRequests(
	first: number = 100,
): Promise<MaintenanceRequest[]> {
	const variables: GetAllMaintenanceRequestsQueryVariables = { first };
	const data = await getDataSDK();
	const result = await data.graphql?.<
		GetAllMaintenanceRequestsQuery,
		GetAllMaintenanceRequestsQueryVariables
	>(GET_ALL_MAINTENANCE_REQUESTS, variables);

	if (result?.errors?.length) {
		const errorMessages = result.errors.map((e) => e.message).join("; ");
		throw new Error(`GraphQL Error: ${errorMessages}`);
	}

	const requests =
		result?.data?.uiapi?.query?.Maintenance_Request__c?.edges?.map((edge: any) =>
			transformMaintenanceTaskFull(edge?.node),
		) || [];
	return requests;
}

// Helper function to transform maintenance request data
function transformMaintenanceRequest(node: any): MaintenanceRequest {
	const scheduledDate = node.Scheduled__c?.value
		? new Date(node.Scheduled__c.value).toLocaleString()
		: undefined;

	return {
		id: node.Id,
		propertyAddress: node.Property__r?.Address__c?.value || "Unknown Address",
		issueType: node.Type__c?.value || "General",
		priority: node.Priority__c?.value?.toLowerCase() || "medium",
		status: node.Status__c?.value?.toLowerCase() || "new",
		assignedWorker: undefined,
		scheduledDateTime: scheduledDate,
		description: node.Description__c?.value || "",
		tenantName: node.User__r?.Name?.value || "Unknown",
	};
}

// Helper function to transform maintenance request data with all fields for maintenance page
function transformMaintenanceTaskFull(node: any): MaintenanceRequest {
	const scheduledDate = node.Scheduled__c?.value ? new Date(node.Scheduled__c.value) : null;
	const formattedDate = scheduledDate
		? scheduledDate.toLocaleDateString("en-US", { month: "short", day: "numeric" }) +
			", " +
			scheduledDate.toLocaleTimeString("en-US", {
				hour: "numeric",
				minute: "2-digit",
				hour12: true,
			})
		: undefined;

	// Get image URL from ContentDocumentLinks
	const imageVersionId =
		node.ContentDocumentLinks?.edges?.[0]?.node?.ContentDocument?.LatestPublishedVersionId?.value;
	const imageUrl = imageVersionId
		? `/sfc/servlet.shepherd/version/download/${imageVersionId}`
		: undefined;

	// Get tenant unit from Property
	const tenantUnit = node.Property__r?.Name?.value || node.Property__r?.Address__c?.value;

	// Get assigned worker name from Owner
	const assignedWorkerName = node.Owner?.Name?.value;

	return {
		id: node.Id,
		propertyAddress: node.Property__r?.Address__c?.value || "Unknown Address",
		issueType: node.Type__c?.value || "General",
		priority: node.Priority__c?.value?.toLowerCase() || "medium",
		status: node.Status__c?.value?.toLowerCase().replace(" ", "_") || "new",
		assignedWorker: assignedWorkerName,
		scheduledDateTime: scheduledDate?.toLocaleString(),
		description: node.Description__c?.value || "",
		tenantName: node.User__r?.Name?.value || "Unknown",
		imageUrl,
		tenantUnit,
		assignedWorkerName,
		assignedWorkerOrg: "ABC Diamond Technicians", // This would come from a related object in real scenario
		formattedDate,
	};
}
