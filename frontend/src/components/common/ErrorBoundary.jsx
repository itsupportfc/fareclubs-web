import { Component } from "react";

export default class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError() {
        // called during render - switches to fallback UI
        return { hasError: true };
    }

    componentDidCatch(error, info) {
        // called after render - log for debugging
        // in produciton, replace with Sentry or your error tracking service
        if (import.meta.env.DEV) {
            console.log("ErrorBoundary caught:", error, info.componentStack);
        }
    }

    render() {
        if (this.state.hasError) {
            //Custom fallback if provided as prop, otherwise default
            if (this.props.fallback) return this.props.fallback;
            return (
                <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4 text-center">
                    <div className="text-5xl mb-4">✈️</div>
                    <h1 className="text-2xl font-bold text-gray-800 mb-2">
                        Something went wrong
                    </h1>
                    <p className="text-gray-500 mb-6 max-w-md">
                        We hit an unexpected error. If you were booking, your
                        payment is safe — please check your email for
                        confirmation.
                    </p>
                    <button
                        onClick={() => (window.location.href = "/")}
                        className="px-6 py-3 bg-gradient-to-r from-[#FF2E57] to-[#FF6B35] text-white font-semibold rounded-xl hover:shadow-lg transition"
                    >
                        Back to Home
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}
