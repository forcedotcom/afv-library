import React from "react";
import { Check } from "lucide-react";

interface StatusBadgeProps {
	status: "new" | "assigned" | "scheduled" | "in_progress" | "completed";
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
	const styles = {
		new: "bg-pink-100 text-pink-700",
		assigned: "bg-purple-100 text-purple-700",
		scheduled: "bg-blue-100 text-blue-700",
		in_progress: "bg-yellow-100 text-yellow-700",
		completed: "bg-green-100 text-green-700",
	};

	const labels = {
		new: "Needs Action",
		assigned: "Assigned",
		scheduled: "Scheduled",
		in_progress: "In Progress",
		completed: "Completed",
	};

	const showCheckmark = status === "completed";
	const showDot = status === "new" || status === "in_progress";

	return (
		<span
			className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium ${styles[status]}`}
		>
			{showCheckmark && <Check className="w-4 h-4" />}
			{showDot && <span className="w-2 h-2 rounded-full bg-current" />}
			{labels[status]}
		</span>
	);
};
