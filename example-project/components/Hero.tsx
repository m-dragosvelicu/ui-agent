// Generic hero section - every SaaS looks like this
import React from 'react';

export function Hero() {
  return (
    <section className="py-20 px-4 text-center">
      <h1 className="text-5xl font-bold mb-4">
        The Modern Platform for Teams
      </h1>
      <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
        Streamline your workflow, boost productivity, and collaborate
        seamlessly with our all-in-one solution.
      </p>
      <div className="flex gap-4 justify-center">
        <button className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600">
          Get Started Free
        </button>
        <button className="border border-gray-300 px-6 py-3 rounded-lg hover:bg-gray-50">
          Watch Demo
        </button>
      </div>
    </section>
  );
}
