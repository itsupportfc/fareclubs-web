import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { UserCircle } from "lucide-react";
import Navbar from "../components/Home/Navbar";
import { getCurrentUser } from "../components/api/auth";

export default function ProfilePage() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [needsLogin, setNeedsLogin] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("access_token");

        if (!token) {
            setNeedsLogin(true);
            setLoading(false);
            return;
        }

        getCurrentUser(token)
            .then(setUser)
            .catch(() => {
                localStorage.removeItem("access_token");
                setNeedsLogin(true);
            })
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="min-h-screen flex items-center justify-center px-4 pt-24">
                <div className="w-full max-w-xl bg-white border border-gray-100 rounded-xl shadow-sm p-6">
                    <div className="text-center mb-6">
                        <div className="mx-auto mb-4 h-14 w-14 rounded-full bg-red-50 flex items-center justify-center">
                            <UserCircle className="h-8 w-8 text-[#FF2E57]" />
                        </div>

                        <h1 className="font-display text-2xl font-bold text-gray-900">
                            My Profile
                        </h1>

                        <p className="text-sm text-gray-500 mt-1">
                            View your Fareclubs account details.
                        </p>
                    </div>

                    {loading && (
                        <p className="text-center text-gray-500">
                            Loading profile...
                        </p>
                    )}

                    {!loading && needsLogin && (
                        <div className="text-center">
                            <p className="text-gray-600">
                                Please sign in to view your profile. You can
                                still search and book flights without signing
                                in.
                            </p>

                            <Link
                                to="/login"
                                className="mt-6 inline-flex rounded-lg bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] px-6 py-3 text-sm font-semibold text-white hover:shadow-md transition"
                            >
                                Sign In
                            </Link>
                        </div>
                    )}

                    {!loading && user && (
                        <div className="space-y-4">
                            <ProfileField
                                label="Username"
                                value={user.username}
                            />
                            <ProfileField label="Email" value={user.email} />
                            <ProfileField
                                label="Account Status"
                                value={user.is_active ? "Active" : "Inactive"}
                            />

                            <Link
                                to="/"
                                className="mt-6 inline-flex w-full justify-center rounded-lg border border-gray-200 px-6 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition"
                            >
                                Back to Flights
                            </Link>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

function ProfileField({ label, value }) {
    return (
        <div className="rounded-lg border border-gray-100 bg-gray-50 px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
                {label}
            </p>
            <p className="mt-1 font-semibold text-gray-800">{value || "--"}</p>
        </div>
    );
}
