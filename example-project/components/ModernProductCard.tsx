
import React, { useState } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';

interface ModernProductCardProps {
  title: string;
  price: number;
  image: string;
  description: string;
}

export function ModernProductCard({ title, price, image, description }: ModernProductCardProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [isAdded, setIsAdded] = useState(false);

  // 3D Tilt Effect Logic
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const cardX = useSpring(mouseX, { stiffness: 300, damping: 40 });
  const cardY = useSpring(mouseY, { stiffness: 300, damping: 40 });

  const rotateX = useTransform(cardY, [-0.5, 0.5], ['10deg', '-10deg']);
  const rotateY = useTransform(cardX, [-0.5, 0.5], ['-10deg', '10deg']);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const xPct = mouseX / width - 0.5;
    const yPct = mouseY / height - 0.5;
    cardX.set(xPct);
    cardY.set(yPct);
  };

  const handleMouseLeave = () => {
    cardX.set(0);
    cardY.set(0);
  };

  // Add to Cart Logic
  const handleAddToCart = () => {
    setIsAdding(true);
    setTimeout(() => {
      setIsAdding(false);
      setIsAdded(true);
      setTimeout(() => setIsAdded(false), 2000); // Reset after 2 seconds
    }, 1500);
  };

  return (
    <motion.div
      className="relative w-full max-w-sm rounded-xl bg-white/30 backdrop-blur-sm shadow-lg"
      style={{
        transformStyle: 'preserve-3d',
        rotateX,
        rotateY,
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div className="p-6">
        <motion.div
          className="w-full h-52 mb-4"
          style={{
            transform: 'translateZ(50px)',
            transformStyle: 'preserve-3d',
          }}
        >
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover rounded-lg shadow-md"
          />
        </motion.div>
        
        <motion.h3 
          className="text-2xl font-bold text-gray-800"
          style={{ transform: 'translateZ(40px)' }}
        >
          {title}
        </motion.h3>
        
        <motion.p 
          className="text-gray-600 text-sm mt-2"
          style={{ transform: 'translateZ(30px)' }}
        >
          {description}
        </motion.p>

        <div className="flex justify-between items-center mt-6">
          <motion.span 
            className="text-3xl font-black text-gray-900"
            style={{ transform: 'translateZ(20px)' }}
          >
            ${price}
          </motion.span>
          
          <motion.button
            onClick={handleAddToCart}
            disabled={isAdding || isAdded}
            className="px-6 py-3 rounded-full font-semibold text-white transition-colors duration-300"
            style={{ 
                transform: 'translateZ(20px)',
                background: isAdded ? '#28a745' : isAdding ? '#6c757d' : '#007bff',
            }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {isAdding ? 'Adding...' : isAdded ? 'Added!' : 'Add to Cart'}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}

// NOTE: To make this component work, you'll need to install framer-motion:
// npm install framer-motion
//
// Also, the backdrop-blur effect requires your parent container to have a background image or color.
// For example, you could wrap this card in a div with a class like: `bg-gradient-to-br from-indigo-100 to-purple-200`

