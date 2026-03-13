import React from "react";
import { Toaster } from "sonner";
import AppRouter from "./router/AppRouter";

export default function App() {
  return (
    <>
      <Toaster position="top-center" richColors />
      <AppRouter />
    </>
  );
}
