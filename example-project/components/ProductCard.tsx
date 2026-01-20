// A basic product card component - feels dated and generic
import React from 'react';

interface ProductCardProps {
  title: string;
  price: number;
  image: string;
  description: string;
  onAddToCart: () => void;
}

export function ProductCard({ title, price, image, description, onAddToCart }: ProductCardProps) {
  return (
    <div className="border rounded-lg p-4 shadow-sm">
      <img
        src={image}
        alt={title}
        className="w-full h-48 object-cover rounded"
      />
      <h3 className="text-lg font-semibold mt-2">{title}</h3>
      <p className="text-gray-600 text-sm mt-1">{description}</p>
      <div className="flex justify-between items-center mt-4">
        <span className="text-xl font-bold">${price}</span>
        <button
          onClick={onAddToCart}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Add to Cart
        </button>
      </div>
    </div>
  );
}
