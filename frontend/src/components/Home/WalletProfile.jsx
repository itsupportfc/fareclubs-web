import { useEffect, useRef, useState } from "react";
import {
    ChevronDown,
    Home,
    LogIn,
    LogOut,
    UserCircle,
    UserPlus,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { getCurrentUser } from "../api/auth";

const WalletProfile = () => {
    const navigate = useNavigate();
    const [open, setOpen] = useState(false);
    const [user, setUser] = useState(null);
    const dropdownRef = useRef(null);

    const displayName = user?.username || "Guest";
    const firstLetter = user?.username?.charAt(0).toUpperCase() || "G";

    useEffect(() => {
        const token = localStorage.getItem("access_token");

        if (!token) return;

        getCurrentUser(token)
            .then(setUser)
            .catch(() => {
                localStorage.removeItem("access_token");
                setUser(null);
            });
    }, []);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(e.target)
            ) {
                setOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () =>
            document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleLogout = () => {
        localStorage.removeItem("access_token");
        setUser(null);
        setOpen(false);
        toast.success("Logged out successfully");
        navigate("/");
    };

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                type="button"
                onClick={() => setOpen((value) => !value)}
                className="flex items-center space-x-2 bg-white cursor-pointer rounded-full px-2 sm:px-3 py-1 hover:shadow-sm transition"
            >
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[#eb0066] to-[#007aff] text-white flex items-center justify-center font-semibold text-sm">
                    {firstLetter}
                </div>

                <span className="hidden sm:inline text-sm font-medium text-gray-700">
                    {displayName}
                </span>

                <ChevronDown
                    className={`w-4 h-4 text-gray-500 transition-transform ${
                        open ? "rotate-180" : ""
                    }`}
                />
            </button>

            {open && (
                <div className="absolute sm:right-0 mt-2 w-52 bg-white border border-gray-200 rounded-lg shadow-lg z-50 left-1/2 sm:left-auto sm:transform-none -translate-x-1/2 sm:translate-x-0">
                    <ul className="py-2 text-gray-700 text-sm">
                        <MenuLink
                            to="/"
                            icon={Home}
                            onClick={() => setOpen(false)}
                        >
                            Home
                        </MenuLink>

                        {user ? (
                            <>
                                <MenuLink
                                    to="/profile"
                                    icon={UserCircle}
                                    onClick={() => setOpen(false)}
                                >
                                    My Profile
                                </MenuLink>

                                <hr className="my-1 border-gray-200" />

                                <li
                                    onClick={handleLogout}
                                    className="flex items-center gap-3 px-4 py-2 hover:bg-red-50 text-red-600 cursor-pointer"
                                >
                                    <LogOut className="w-4 h-4" />
                                    Logout
                                </li>
                            </>
                        ) : (
                            <>
                                <hr className="my-1 border-gray-200" />

                                <MenuLink
                                    to="/login"
                                    icon={LogIn}
                                    onClick={() => setOpen(false)}
                                >
                                    Sign In
                                </MenuLink>

                                <MenuLink
                                    to="/signup"
                                    icon={UserPlus}
                                    onClick={() => setOpen(false)}
                                >
                                    Create Account
                                </MenuLink>
                            </>
                        )}
                    </ul>
                </div>
            )}
        </div>
    );
};

function MenuLink({ to, icon: Icon, children, onClick }) {
    return (
        <li>
            <Link
                to={to}
                onClick={onClick}
                className="flex items-center gap-3 px-4 py-2 hover:bg-gray-100"
            >
                <Icon className="w-4 h-4 text-gray-600" />
                {children}
            </Link>
        </li>
    );
}

export default WalletProfile;
