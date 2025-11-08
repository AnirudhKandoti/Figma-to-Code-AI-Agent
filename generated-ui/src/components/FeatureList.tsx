import React from 'react';

interface Feature {
  title: string;
  description: string;
}

interface FeatureListProps {
  features: Feature[];
}

const FeatureList: React.FC<FeatureListProps> = ({ features }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-2xl font-semibold text-gray-900 mb-4">Features</h3>
      <ul>
        {features.map((feature, index) => (
          <li key={index} className="mb-4">
            <h4 className="text-xl font-semibold text-gray-800">{feature.title}</h4>
            <p className="text-gray-600">{feature.description}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default FeatureList;