
import { GoogleGenAI, Type } from "@google/genai";
import type { RecommendedModel } from '../types';

const getRecommendedModels = async (existingModels: string): Promise<RecommendedModel[]> => {
    if (!process.env.API_KEY) {
        throw new Error("API_KEY environment variable not set");
    }

    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

    const prompt = `
    You are an expert on local LLMs and Ollama. A user has provided a list of Ollama models they already have.
    Your task is to recommend 3 to 5 new, interesting, and useful Ollama models that are small (ideally under 4GB) and can run efficiently on a CPU.
    Do not recommend any models from the user's existing list.
    Focus on models that are good for tasks like coding assistance, general chat, or function calling.

    User's existing models:
    ---
    ${existingModels}
    ---

    Provide your recommendations in a JSON array format.
    For each model, include its name, approximate size (e.g., "2.7B", "3B", "770MB"), a brief one-sentence description of its primary use case, and the exact 'ollama run' command to pull and run it.
  `;

    try {
        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.ARRAY,
                    items: {
                        type: Type.OBJECT,
                        properties: {
                            name: {
                                type: Type.STRING,
                                description: "The official name of the Ollama model (e.g., 'phi3:mini').",
                            },
                            size: {
                                type: Type.STRING,
                                description: "The approximate size of the model (e.g., '2.2 GB').",
                            },
                            description: {
                                type: Type.STRING,
                                description: "A brief, one-sentence summary of what the model is best for.",
                            },
                            pullCommand: {
                                type: Type.STRING,
                                description: "The exact command to run the model using Ollama (e.g., 'ollama run phi3:mini').",
                            },
                        },
                        required: ["name", "size", "description", "pullCommand"],
                    },
                },
            },
        });
        
        const jsonText = response.text.trim();
        const models = JSON.parse(jsonText) as RecommendedModel[];
        return models;

    } catch (error) {
        console.error("Error fetching recommended models from Gemini API:", error);
        throw new Error("Failed to get recommendations. Please check the console for more details.");
    }
};

export default getRecommendedModels;
