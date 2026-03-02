import React from "react";
import { Link, useLocation } from "react-router";
import dashboardIcon from "../assets/icons/dashboard.svg";
import filesIcon from "../assets/icons/files.svg";
import propertiesIcon from "../assets/icons/properties.svg";
import maintenanceIcon from "../assets/icons/maintenance.svg";
import usersIcon from "../assets/icons/users.svg";
import supportIcon from "../assets/icons/support.svg";

interface NavItem {
	path: string;
	icon: string;
	label: string;
}

const navItems: NavItem[] = [
	{ path: "/", icon: dashboardIcon, label: "Dashboard" },
	{ path: "/files", icon: filesIcon, label: "Files" },
	{ path: "/properties", icon: propertiesIcon, label: "Properties" },
	{ path: "/maintenance", icon: maintenanceIcon, label: "Maintenance" },
	{ path: "/users", icon: usersIcon, label: "Users" },
	{ path: "/support", icon: supportIcon, label: "Support" },
];

export const VerticalNav: React.FC = () => {
	const location = useLocation();

	const isActive = (path: string) => {
		if (path === "/") {
			return location.pathname === "/";
		}
		return location.pathname.startsWith(path);
	};

	return (
		<div className="flex flex-col w-24 bg-white border-r border-gray-200 py-8 space-y-4">
			{navItems.map((item) => (
				<Link
					key={item.path}
					to={item.path}
					className={`flex flex-col items-center justify-center gap-2 py-4 px-2 transition-colors ${
						isActive(item.path)
							? "bg-purple-100 text-purple-700 border-l-4 border-purple-700"
							: "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
					}`}
					title={item.label}
				>
					<img src={item.icon} alt={item.label} className="w-6 h-6" />
					<span className="text-xs font-medium">{item.label}</span>
				</Link>
			))}
		</div>
	);
};
