import React from "react";

interface AnalyticsTileProps {
	title: string;
	value: number | string;
	onClick?: () => void;
}

export const AnalyticsTile: React.FC<AnalyticsTileProps> = ({ title, value, onClick }) => {
	return (
		<div
			className={`bg-white rounded-lg shadow p-6 text-center ${
				onClick ? "cursor-pointer hover:shadow-lg transition-shadow" : ""
			}`}
			onClick={onClick}
			role={onClick ? "button" : undefined}
			tabIndex={onClick ? 0 : undefined}
			onKeyDown={(e) => {
				if (onClick && (e.key === "Enter" || e.key === " ")) {
					e.preventDefault();
					onClick();
				}
			}}
		>
			<h3 className="text-sm font-medium text-gray-600 mb-2">{title}</h3>
			<p className="text-3xl font-bold text-gray-900">{value}</p>
		</div>
	);
};
