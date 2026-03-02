import { Outlet } from "react-router";
import { TopBar } from "./components/TopBar.js";
import { VerticalNav } from "./components/VerticalNav.js";

export default function AppLayout() {
	return (
		<div className="flex flex-col h-screen">
			{/* Top Bar */}
			<TopBar />

			{/* Main Content Area with Sidebar */}
			<div className="flex flex-1 overflow-hidden">
				{/* Vertical Navigation */}
				<VerticalNav />

				{/* Page Content */}
				<main className="flex-1 overflow-auto">
					<Outlet />
				</main>
			</div>
		</div>
	);
}
