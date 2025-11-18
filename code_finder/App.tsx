
import React, { useState, useCallback } from 'react';
import type { RecommendedModel } from './types';
import getRecommendedModels from './services/geminiService';
import ModelCard from './components/ModelCard';
import Spinner from './components/Spinner';

const initialModels = `nomic-embed-text:latest        0a109f422b47  274 MB  3 weeks ago
phi3:arcadian                  75dda6037bb6  2.2 GB  3 weeks ago
llama3.2:3b                    a80c4f17acd5  2.0 GB  4 weeks ago
falcon:7b                      4280f7257e73  4.2 GB  4 weeks ago
phi3:latest                    4f2222927938  2.2 GB  4 weeks ago
deepseek-coder:1.3b            3ddd2d3fc8d2  776 MB  4 weeks ago
deepseek-r1:1.5b               e0979632db5a  1.1 GB  4 weeks ago
mistral:7b                     6577803aa9a0  4.4 GB  4 weeks ago
LlaVa:latest                   8dd30f6b0cb1  4.7 GB  4 weeks ago
phi:latest                     e2fd6321a5fe  1.6 GB  4 weeks ago
saikatkumardey/tinyllama:Q8_0  1f8f12e9b667  1.2 GB  7 hours ago
starcoder:1b                   77e6c46054d9  726 MB  21 minutes ago`;
const App: React.FC = () => {
  const [existingModels, setExistingModels] = useState<string>(initialModels);
  const [recommendedModels, setRecommendedModels] = useState<RecommendedModel[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFindModels = useCallback(async () => {
    if (!existingModels.trim()) {
      setError("Please enter your existing models.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setRecommendedModels([]);

    try {
      const models = await getRecommendedModels(existingModels);
      setRecommendedModels(models);
    } catch (err: any) {
      setError(err.message || "An unknown error occurred.");
    } finally {
      setIsLoading(false);
    }
  }, [existingModels]);

  return (
    <div className="min-h-screen bg-base-100 font-sans p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-4xl sm:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-brand-primary to-brand-secondary mb-2">
            Ollama Model Finder
          </h1>
          <p className="text-lg text-gray-400">
            Discover new, small, CPU-friendly Ollama models tailored for you.
          </p>
        </header>

        <main>
          <div className="bg-base-200 p-6 rounded-lg shadow-xl mb-8">
            <label htmlFor="existing-models" className="block text-lg font-medium text-gray-200 mb-2">
              Your Existing Ollama Models
            </label>
            <textarea
              id="existing-models"
              rows={10}
              className="w-full p-3 bg-base-300 text-gray-300 rounded-md border border-base-300 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition-shadow duration-200 placeholder-gray-500 font-mono text-sm"
              placeholder="Paste the output of `ollama list` here..."
              value={existingModels}
              onChange={(e) => setExistingModels(e.target.value)}
            />
            <div className="mt-4 flex justify-end">
              <button
                onClick={handleFindModels}
                disabled={isLoading}
                className="px-6 py-3 bg-brand-primary text-white font-semibold rounded-lg shadow-md hover:bg-brand-primary/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-base-200 focus:ring-brand-primary disabled:bg-gray-500 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:scale-100"
              >
                {isLoading ? 'Searching...' : 'Find New Models'}
              </button>
            </div>
          </div>
          
          {error && (
             <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg text-center" role="alert">
                <strong className="font-bold">Error: </strong>
                <span className="block sm:inline">{error}</span>
            </div>
          )}

          {isLoading && <Spinner />}

          {recommendedModels.length > 0 && (
             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
               {recommendedModels.map((model) => (
                 <ModelCard key={model.name} model={model} />
               ))}
             </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
