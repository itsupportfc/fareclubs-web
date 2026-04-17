import React from "react";
import { Toaster } from "sonner";
import AppRouter from "./router/AppRouter";
import ErrorBoundary from "./components/common/ErrorBoundary";

export default function App() {
    return (
        <ErrorBoundary>
            <Toaster position="top-center" richColors />
            <AppRouter />
        </ErrorBoundary>
    );
}
