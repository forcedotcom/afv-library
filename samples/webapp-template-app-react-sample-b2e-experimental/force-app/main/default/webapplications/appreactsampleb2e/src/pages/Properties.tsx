import { useEffect, useState } from "react";
import { getProperties } from "../api/properties.js";
import type { Property } from "../lib/types.js";
import { PropertyCard } from "../components/PropertyCard.js";
import { Button } from "@/components/ui/button";

export default function Properties() {
	const [properties, setProperties] = useState<Property[]>([]);
	const [loading, setLoading] = useState(true);
	const [loadingMore, setLoadingMore] = useState(false);
	const [hasNextPage, setHasNextPage] = useState(false);
	const [endCursor, setEndCursor] = useState<string | null>(null);

	useEffect(() => {
		loadProperties();
	}, []);

	const loadProperties = async () => {
		try {
			setLoading(true);
			const result = await getProperties(12);
			setProperties(result.properties);
			setHasNextPage(result.pageInfo.hasNextPage);
			setEndCursor(result.pageInfo.endCursor!);
		} catch (error) {
			console.error("Error loading properties:", error);
		} finally {
			setLoading(false);
		}
	};

	const loadMoreProperties = async () => {
		if (!endCursor) return;

		try {
			setLoadingMore(true);
			const result = await getProperties(12, endCursor);
			setProperties((prev) => [...prev, ...result.properties]);
			setHasNextPage(result.pageInfo.hasNextPage);
			setEndCursor(result.pageInfo.endCursor!);
		} catch (error) {
			console.error("Error loading more properties:", error);
		} finally {
			setLoadingMore(false);
		}
	};

	const handlePropertyClick = (property: Property) => {
		console.log("Property clicked:", property);
		// TODO: Navigate to property details page
	};

	if (loading) {
		return (
			<div className="flex items-center justify-center h-screen bg-gray-50">
				<div className="text-lg text-gray-600">Loading properties...</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gray-50 p-8">
			<div className="max-w-7xl mx-auto">
				{/* Properties Grid */}
				{properties.length === 0 ? (
					<div className="text-center py-12">
						<p className="text-gray-500 text-lg">No properties found</p>
					</div>
				) : (
					<>
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
							{properties.map((property) => (
								<PropertyCard key={property.id} property={property} onClick={handlePropertyClick} />
							))}
						</div>

						{/* Load More Button */}
						{hasNextPage && (
							<div className="flex justify-center mt-8">
								<Button
									onClick={loadMoreProperties}
									disabled={loadingMore}
									className="px-8 py-3 bg-purple-700 hover:bg-purple-800 text-white rounded-lg font-medium transition-colors"
								>
									{loadingMore ? "Loading..." : "Load More"}
								</Button>
							</div>
						)}
					</>
				)}
			</div>
		</div>
	);
}
