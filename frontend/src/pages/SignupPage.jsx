import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus } from "lucide-react";
import { toast } from "sonner";
import Navbar from "../components/Home/Navbar";
import { signupUser } from "../components/api/auth";

export default function SignupPage() {
    const navigate = useNavigate();
    const [form, setForm] = useState({
        username: "",
        email: "",
        password: "",
    });
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            await signupUser(form);
            toast.success("Account created. Please sign in.");
            navigate("/login");
        } catch (err) {
            toast.error(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="min-h-screen flex items-center justify-center px-4 pt-24">
                <div className="w-full max-w-md bg-white border border-gray-100 rounded-xl shadow-sm p-6">
                    <div className="text-center mb-6">
                        <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-red-50 flex items-center justify-center">
                            <UserPlus className="h-6 w-6 text-[#FF2E57]" />
                        </div>

                        <h1 className="font-display text-2xl font-bold text-gray-900">
                            Create Account
                        </h1>

                        <p className="text-sm text-gray-500 mt-1">
                            Create an account to access your profile. Flight
                            booking remains available without signing in.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="text-sm font-medium text-gray-700">
                                Username
                            </label>
                            <input
                                name="username"
                                value={form.username}
                                onChange={handleChange}
                                required
                                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 outline-none focus:border-[#FF2E57] focus:ring-2 focus:ring-pink-100"
                            />
                        </div>

                        <div>
                            <label className="text-sm font-medium text-gray-700">
                                Email
                            </label>
                            <input
                                name="email"
                                type="email"
                                value={form.email}
                                onChange={handleChange}
                                required
                                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 outline-none focus:border-[#FF2E57] focus:ring-2 focus:ring-pink-100"
                            />
                        </div>

                        <div>
                            <label className="text-sm font-medium text-gray-700">
                                Password
                            </label>
                            <input
                                name="password"
                                type="password"
                                value={form.password}
                                onChange={handleChange}
                                required
                                minLength={6}
                                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 outline-none focus:border-[#FF2E57] focus:ring-2 focus:ring-pink-100"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-lg bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] py-3 text-sm font-semibold text-white hover:shadow-md disabled:opacity-60 transition"
                        >
                            {loading ? "Creating account..." : "Create Account"}
                        </button>
                    </form>

                    <p className="text-sm text-center text-gray-500 mt-5">
                        Already have an account?{" "}
                        <Link
                            to="/login"
                            className="font-semibold text-[#FF2E57]"
                        >
                            Sign in
                        </Link>
                    </p>
                </div>
            </main>
        </div>
    );
}
