import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import { getAllMaintenanceRequests } from "../api/maintenance.js";
import type { MaintenanceRequest } from "../lib/types.js";
import { UserAvatar } from "../components/UserAvatar.js";
import { PriorityBadge } from "../components/PriorityBadge.js";
import { StatusBadge } from "../components/StatusBadge.js";

export default function Maintenance() {
	const [requests, setRequests] = useState<MaintenanceRequest[]>([]);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		loadMaintenanceRequests();
	}, []);

	const loadMaintenanceRequests = async () => {
		try {
			setLoading(true);
			const data = await getAllMaintenanceRequests();
			setRequests(data);
		} catch (error) {
			console.error("Error loading maintenance requests:", error);
		} finally {
			setLoading(false);
		}
	};

	if (loading) {
		return (
			<div className="flex items-center justify-center h-screen bg-gray-50">
				<div className="text-lg text-gray-600">Loading maintenance requests...</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gray-50 p-8">
			<div className="max-w-7xl mx-auto">
				{/* Table Header */}
				<div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
					<div className="grid grid-cols-12 gap-4 px-6 py-4 bg-gray-50 border-b border-gray-200">
						<div className="col-span-4 flex items-center gap-2">
							<span className="text-sm font-semibold text-purple-700 uppercase tracking-wide">
								Maintenance Task
							</span>
							<ChevronDown className="w-4 h-4 text-purple-700" />
						</div>
						<div className="col-span-2">
							<span className="text-sm font-semibold text-purple-700 uppercase tracking-wide">
								Tenant Unit
							</span>
						</div>
						<div className="col-span-2">
							<span className="text-sm font-semibold text-purple-700 uppercase tracking-wide">
								Assigned to
							</span>
						</div>
						<div className="col-span-2">
							<span className="text-sm font-semibold text-purple-700 uppercase tracking-wide">
								Date
							</span>
						</div>
						<div className="col-span-2">
							<span className="text-sm font-semibold text-purple-700 uppercase tracking-wide">
								Status
							</span>
						</div>
					</div>

					{/* Table Rows */}
					<div className="divide-y divide-gray-200">
						{requests.length === 0 ? (
							<div className="text-center py-12 text-gray-500">No maintenance requests found</div>
						) : (
							requests.map((request) => (
								<div
									key={request.id}
									className="grid grid-cols-12 gap-4 px-6 py-5 hover:bg-gray-50 transition-colors"
								>
									{/* Maintenance Task */}
									<div className="col-span-4 flex items-center gap-4">
										{/* Task Image */}
										<div className="w-16 h-16 rounded-lg bg-gray-200 flex-shrink-0 overflow-hidden">
											{request.imageUrl ? (
												<img
													src={request.imageUrl}
													alt={request.description}
													className="w-full h-full object-cover"
												/>
											) : (
												<div className="w-full h-full flex items-center justify-center text-gray-400">
													<span className="text-2xl">🔧</span>
												</div>
											)}
										</div>

										{/* Task Details */}
										<div className="flex-1 min-w-0">
											<div className="flex items-center gap-2 mb-1">
												<h3 className="font-semibold text-gray-900 truncate">
													{request.description}
												</h3>
												{request.priority && <PriorityBadge priority={request.priority} />}
											</div>
											<p className="text-sm text-gray-500">By Tenant</p>
										</div>
									</div>

									{/* Tenant Unit */}
									<div className="col-span-2 flex items-center">
										<div className="flex items-center gap-3">
											<UserAvatar name={request.tenantName || "Unknown"} size="md" />
											<div className="min-w-0">
												<p className="text-sm font-medium text-gray-900 truncate">
													{request.tenantName || "Unknown"}
												</p>
												<p className="text-sm text-gray-500 truncate">
													{request.tenantUnit || request.propertyAddress}
												</p>
											</div>
										</div>
									</div>

									{/* Assigned to */}
									<div className="col-span-2 flex items-center">
										{request.assignedWorkerName ? (
											<div className="flex items-center gap-3">
												<UserAvatar name={request.assignedWorkerName} size="md" />
												<div className="min-w-0">
													<p className="text-sm font-medium text-gray-900 truncate">
														{request.assignedWorkerName}
													</p>
													<p className="text-sm text-gray-500 truncate">
														{request.assignedWorkerOrg}
													</p>
												</div>
											</div>
										) : (
											<span className="text-sm text-gray-400">Unassigned</span>
										)}
									</div>

									{/* Date */}
									<div className="col-span-2 flex items-center">
										<div className="flex items-center gap-2 text-sm text-gray-700">
											<svg
												className="w-4 h-4"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													strokeLinecap="round"
													strokeLinejoin="round"
													strokeWidth={2}
													d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
												/>
											</svg>
											<span>{request.formattedDate || "Not scheduled"}</span>
										</div>
									</div>

									{/* Status */}
									<div className="col-span-2 flex items-center">
										<StatusBadge status={request.status} />
									</div>
								</div>
							))
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
