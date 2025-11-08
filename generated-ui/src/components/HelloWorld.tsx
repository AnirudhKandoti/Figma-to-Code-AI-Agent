import React from 'react';

interface HelloWorldProps {
  text: string;
}

const HelloWorld: React.FC<HelloWorldProps> = ({ text }) => {
  return (
    <div className="flex items-center justify-center h-screen">
      <h1 className="text-3xl font-bold underline">
        {text}
      </h1>
    </div>
  );
};

export default HelloWorld;