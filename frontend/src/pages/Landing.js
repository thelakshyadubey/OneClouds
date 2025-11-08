import React from "react";
import { Link } from "react-router-dom";
import { FaGoogle, FaDropbox, FaMicrosoft, FaCloud } from "react-icons/fa";

const Landing = () => {
  return (
    <div className="min-h-screen bg-oc-white">
      {/* Header */}
      <nav className="bg-oc-navy text-oc-white px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <FaCloud className="text-3xl text-oc-teal" />
            <h1 className="text-2xl font-bold">OneClouds</h1>
          </div>
          <Link
            to="/login"
            className="bg-oc-teal text-oc-white px-4 py-2 rounded-md hover:bg-oc-steel transition-colors"
          >
            Login
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-6 pt-16 pb-8">
        <div className="text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-oc-dark mb-6">
            Unify Your
            <span className="text-oc-teal block">Cloud Storage</span>
          </h1>
          <p className="text-xl text-oc-steel mb-8 max-w-3xl mx-auto">
            Access all your files from Google Drive, Dropbox, OneDrive, and more
            in one unified interface. Find duplicates, organize files, and
            manage your cloud storage efficiently.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register"
              className="bg-oc-navy text-oc-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-oc-dark transition-colors"
            >
              Sign Up Now
            </Link>
            <a
              href="#features"
              className="border-2 border-oc-navy text-oc-navy px-8 py-3 rounded-lg text-lg font-medium hover:bg-oc-navy hover:text-oc-white transition-colors"
            >
              Learn More
            </a>
          </div>
        </div>
      </div>

      {/* Supported Providers */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-oc-dark mb-4">
            Connect All Your Cloud Storage
          </h2>
          <p className="text-lg text-oc-steel">
            We support all major cloud storage providers
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="text-center p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <FaGoogle className="text-5xl text-google mx-auto mb-4" /> {/* Keep original color for brand consistency */}
            <h3 className="text-lg font-semibold text-oc-dark">
              Google Drive
            </h3>
            <p className="text-sm text-oc-steel mt-2">
              Access your Google Drive files and photos
            </p>
          </div>

          <div className="text-center p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <FaDropbox className="text-5xl text-dropbox mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-oc-dark">Dropbox</h3>
            <p className="text-sm text-oc-steel mt-2">
              Sync your Dropbox files and folders
            </p>
          </div>

          <div className="text-center p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <FaMicrosoft className="text-5xl text-microsoft mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-oc-dark">OneDrive</h3>
            <p className="text-sm text-oc-steel mt-2">
              Connect your Microsoft OneDrive account
            </p>
          </div>

          <div className="text-center p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <FaCloud className="text-5xl text-terabox mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-oc-dark">
              More Providers
            </h3>
            <p className="text-sm text-oc-steel mt-2">
              Additional providers coming soon
            </p>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div id="features" className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-oc-dark mb-4">
            Powerful Features
          </h2>
          <p className="text-lg text-oc-steel max-w-2xl mx-auto">
            Everything you need to manage your cloud storage efficiently
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center p-6">
            <div className="w-16 h-16 bg-oc-teal/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path className="text-oc-teal"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-oc-dark mb-2">
              Unified File View
            </h3>
            <p className="text-oc-steel">
              See all your files from different cloud storage providers in one
              place
            </p>
          </div>

          <div className="text-center p-6">
            <div className="w-16 h-16 bg-oc-teal/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path className="text-oc-teal"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-oc-dark mb-2">
              Duplicate Detection
            </h3>
            <p className="text-oc-steel">
              Automatically find and remove duplicate files across all your
              cloud storage
            </p>
          </div>

          <div className="text-center p-6">
            <div className="w-16 h-16 bg-oc-teal/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-purple-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path className="text-oc-teal"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" className="text-oc-teal"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-oc-dark mb-2">
              File Preview
            </h3>
            <p className="text-oc-steel">
              Preview your files without downloading them first
            </p>
          </div>

          <div className="text-center p-6">
            <div className="w-16 h-16 bg-oc-teal/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path className="text-oc-teal"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-oc-dark mb-2">
              Smart Filtering
            </h3>
            <p className="text-oc-steel">
              Filter and sort files by type, size, date, or cloud provider
            </p>
          </div>

          <div className="text-center p-6">
            <div className="w-16 h-16 bg-oc-teal/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-yellow-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path className="text-oc-teal"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-oc-dark mb-2">
              Secure Access
            </h3>
            <p className="text-oc-steel">
              Read-only access to your files with secure OAuth authentication
            </p>
          </div>

          <div className="text-center p-6">
            <div className="w-16 h-16 bg-oc-teal/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-indigo-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path className="text-oc-teal"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-oc-dark mb-2">
              Fast & Efficient
            </h3>
            <p className="text-oc-steel">
              Quick synchronization and metadata-only processing for speed
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-oc-dark text-oc-white py-8">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <FaCloud className="text-2xl" />
            <h3 className="text-xl font-bold">OneClouds</h3>
          </div>
          <p className="text-oc-steel">
            Simplifying cloud storage management for everyone
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
