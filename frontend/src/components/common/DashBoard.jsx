import React from "react";
import Navbar from "../Home/Navbar";
import SearchPanel from "../Home/SearchPanel";
import Cards from "../Home/Cards";
import Footer from "../Home/Footer";

const Dashboard = () => {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50 text-gray-800">
      {/* 🧭 Navbar */}
      <Navbar />

      {/* 🔍 Search Section */}
      <main className="flex-grow container   ">
        <SearchPanel />

        {/* 🪪 Cards Section */}
        
      </main>
      <section className="mt-8 mb-5">
          <Cards />
        </section>
      {/* ⚓ Footer */}
      <Footer />
    </div>
  );
};

export default Dashboard;
