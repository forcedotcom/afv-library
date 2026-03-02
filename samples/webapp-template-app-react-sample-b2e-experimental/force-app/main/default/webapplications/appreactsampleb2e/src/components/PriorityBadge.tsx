import React from "react";

interface PriorityBadgeProps {
	priority: "emergency" | "high" | "medium" | "low";
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority }) => {
	const styles = {
		emergency: "bg-red-100 text-red-700 border-red-200",
		high: "bg-red-100 text-red-700 border-red-200",
		medium: "bg-orange-100 text-orange-700 border-orange-200",
		low: "bg-blue-100 text-blue-700 border-blue-200",
	};

	const labels = {
		emergency: "Emergency",
		high: "High Priority",
		medium: "Medium Priority",
		low: "Low Priority",
	};

	return (
		<span
			className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[priority]}`}
		>
			{labels[priority]}
		</span>
	);
};
