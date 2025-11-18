
import React, { useState } from 'react';
import type { RecommendedModel } from '../types';
import ClipboardIcon from './icons/ClipboardIcon';
import CheckIcon from './icons/CheckIcon';

interface ModelCardProps {
  model: RecommendedModel;
}

const ModelCard: React.FC<ModelCardProps> = ({ model }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(model.pullCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-base-200 rounded-lg shadow-lg p-6 flex flex-col justify-between transition-transform duration-300 hover:scale-105 hover:shadow-brand-primary/20">
      <div>
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-xl font-bold text-gray-100">{model.name}</h3>
          <span className="bg-brand-secondary/20 text-brand-secondary text-sm font-semibold px-3 py-1 rounded-full">{model.size}</span>
        </div>
        <p className="text-gray-400 mb-4">{model.description}</p>
      </div>
      <div>
        <div className="bg-base-300 p-3 rounded-md mb-4">
          <code className="text-gray-300 break-all">{model.pullCommand}</code>
        </div>
        <button
          onClick={handleCopy}
          className={`w-full flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-base-200 transition-colors duration-200 ${
            copied
              ? 'bg-green-600 text-white'
              : 'bg-brand-primary text-white hover:bg-brand-primary/80 focus:ring-brand-primary'
          }`}
        >
          {copied ? (
            <>
              <CheckIcon className="mr-2 h-5 w-5" />
              Copied!
            </>
          ) : (
            <>
              <ClipboardIcon className="mr-2 h-5 w-5" />
              Copy Command
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default ModelCard;
