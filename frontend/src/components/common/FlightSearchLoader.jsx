import { Plane } from "lucide-react"; // import the SVG icon react component

function FlightCardSkeleton() {
    return (
        <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
            {/* 1st row */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full shimmer-bg" />
                    <div className="space-y-1.5">
                        <div className="h-3 w-24 rounded shimmer-bg" />
                        <div className="h-2.5 w-16 rounded shimmer-bg" />
                    </div>
                </div>
                <div className="h-6 w-20 rounded-lg shimmer-bg" />
            </div>
            {/* 2nd row */}
            <div className="flex items-center justify-between">
                <div className="space-y-1">
                    <div className="h-5 w-16 rounded shimmer-bg" />
                    <div className="h-3 w-12 rounded shimmer-bg" />
                </div>
                <div className="flex-1 mx-6 h-px shimmer-bg" />
                <div className="space-y-1 text-right">
                    <div className="h-5 w-16 rounded shimmer-bg" />
                    <div className="h-3 w-12 rounded shimmer-bg" />
                </div>
            </div>
        </div>
    );
}

/* ✈️ Plane Animation */
function PlaneAnimation() {
    return (
        <div className="flex flex-col items-center py-8">
            <div className="w-full max-w-xl relative h-10 mb-3 overflow-hidden">
                {/* Grey base line */}
                <div className="absolute top-1/2 left-0 w-full h-[4px] -translate-y-1/2 bg-gray-200 rounded-full" />

                {/* Moving plane group */}
                <div className="absolute top-1/2 left-0 animate-plane-fly">
                    {/* Trail — solid pink, extends far left so overflow:hidden clips it at the container edge */}
                    <div
                        className="absolute top-1/2 -translate-y-1/2 h-[4px] bg-pink-500 rounded-full"
                        style={{ right: "100%", width: "600px" }}
                    />

                    {/* Plane */}
                    <Plane
                        className="absolute top-1/2 -translate-y-1/2 w-7 h-7 text-pink-600"
                        style={{ rotate: "45deg" }}
                    />
                </div>
            </div>

            <p className="text-gray-500 font-display text-lg">
                Searching for best fares...
            </p>
        </div>
    );
}
// skeletonCount: total number of skeleton cards to display
export default function FlightSearchLoader({ columns = 1, skeletonCount = 6 }) {
    const skeletons = Array.from({ length: skeletonCount }).map((_, i) => (
        <FlightCardSkeleton key={i} />
    ));

    return (
        <>
            <PlaneAnimation />
            {columns === 1 ? (
                <div className="space-y-4">{skeletons}</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                        {skeletons.slice(0, Math.ceil(skeletonCount / 2))}
                    </div>
                    <div className="space-y-4">
                        {skeletons.slice(Math.ceil(skeletonCount / 2))}
                    </div>
                </div>
            )}
        </>
    );
}
