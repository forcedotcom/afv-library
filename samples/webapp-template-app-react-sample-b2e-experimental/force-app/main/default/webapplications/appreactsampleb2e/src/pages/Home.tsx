import { useEffect, useState } from "react";
import { StatCard } from "../components/StatCard.js";
import { IssuesDonutChart } from "../components/IssuesDonutChart.js";
import { MaintenanceTable } from "../components/MaintenanceTable.js";
import { getDashboardMetrics, calculateMetrics } from "../api/dashboard.js";
import { getMaintenanceRequests } from "../api/maintenance.js";
import type { DashboardMetrics, MaintenanceRequest } from "../lib/types.js";

export default function Home() {
	const [metrics, setMetrics] = useState<DashboardMetrics>({
		totalProperties: 0,
		unitsAvailable: 0,
		occupiedUnits: 0,
		topMaintenanceIssue: "",
		topMaintenanceIssueCount: 0,
	});
	const [maintenanceRequests, setMaintenanceRequests] = useState<MaintenanceRequest[]>([]);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		loadDashboardData();
	}, []);

	const loadDashboardData = async () => {
		try {
			setLoading(true);

			// Load metrics
			const { properties } = await getDashboardMetrics();
			setMetrics(calculateMetrics(properties));

			// Load maintenance requests
			const maintenanceData = await getMaintenanceRequests(5);
			setMaintenanceRequests(maintenanceData);
		} catch (error) {
			console.error("Error loading dashboard data:", error);
		} finally {
			setLoading(false);
		}
	};

	const handleViewMaintenance = (id: string) => {
		console.log("View maintenance request:", id);
	};

	// Calculate chart data from maintenance requests
	const calculateChartData = () => {
		const issueCounts: Record<string, number> = {
			Plumbing: 0,
			HVAC: 0,
			Electrical: 0,
			Other: 0,
		};

		maintenanceRequests.forEach((request) => {
			const type = request.issueType;
			if (type === "Plumbing" || type === "HVAC" || type === "Electrical") {
				issueCounts[type]++;
			} else {
				issueCounts.Other++;
			}
		});

		return [
			{ name: "Plumbing", value: issueCounts.Plumbing, color: "#7C3AED" },
			{ name: "HVAC", value: issueCounts.HVAC, color: "#EC4899" },
			{ name: "Electrical", value: issueCounts.Electrical, color: "#14B8A6" },
			{ name: "Other", value: issueCounts.Other, color: "#06B6D4" },
		];
	};

	// Calculate previous month's data (mock for now)
	const getPreviousMetrics = () => ({
		totalProperties: 12,
		unitsAvailable: 78,
		occupiedUnits: 422,
	});

	const previousMetrics = getPreviousMetrics();

	if (loading) {
		return (
			<div className="flex items-center justify-center h-screen bg-gray-50">
				<div className="text-lg text-gray-600">Loading dashboard...</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gray-50">
			{/* Main Content Area */}
			<div className="max-w-7xl mx-auto p-8 space-y-6">
				{/* Search Bar (Desktop) */}
				<div className="hidden md:flex justify-end mb-4">
					<div className="w-96 bg-white rounded-full px-6 py-3 shadow-sm border border-gray-200 flex items-center">
						<input
							type="text"
							placeholder="Search"
							className="flex-1 outline-none text-gray-600"
							disabled
						/>
						<svg
							className="w-5 h-5 text-gray-400"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								strokeLinecap="round"
								strokeLinejoin="round"
								strokeWidth={2}
								d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
							/>
						</svg>
					</div>
				</div>

				{/* Main Layout: 70/30 split */}
				<div className="grid grid-cols-1 lg:grid-cols-[70%_30%] gap-6">
					{/* Left Column: Stat Cards + Maintenance Table */}
					<div className="space-y-6">
						{/* Stat Cards Row */}
						<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
							<StatCard
								title="Total Properties"
								value={metrics.totalProperties}
								trend={{
									value: 20,
									isPositive: true,
								}}
								subtitle={`Last month total ${previousMetrics.totalProperties}`}
							/>
							<StatCard
								title="Units Available"
								value={metrics.unitsAvailable}
								trend={{
									value: 10,
									isPositive: false,
								}}
								subtitle={`Last month total ${previousMetrics.unitsAvailable}/${metrics.totalProperties}`}
							/>
							<StatCard
								title="Occupied Units"
								value={metrics.occupiedUnits}
								trend={{
									value: 5,
									isPositive: true,
								}}
								subtitle={`Last month total ${previousMetrics.occupiedUnits}`}
							/>
						</div>

						{/* Maintenance Requests Table */}
						<MaintenanceTable requests={maintenanceRequests} onView={handleViewMaintenance} />
					</div>

					{/* Right Column: Donut Chart */}
					<div>
						<IssuesDonutChart data={calculateChartData()} />
					</div>
				</div>
			</div>
		</div>
	);
}
