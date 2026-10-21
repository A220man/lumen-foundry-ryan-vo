import { useState, useRef, useCallback, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useAuthStore } from '../stores/authStore';

interface Model {
  id: number;
  name: string;
  model_id: string;
}

interface InferenceResult {
  id: string;
  model_id: number;
  prompt: string;
  generated_text: string;
  finish_reason: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  created_at: number;
}

function Inference() {
  useAuthStore(); // Ensure auth is checked
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<number | null>(null);
  const [prompt, setPrompt] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(512);
  const [stream, setStream] = useState(false);
  const [result, setResult] = useState<InferenceResult | null>(null);
  const [streamingText, setStreamingText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const tokenCountRef = useRef(0);

  useEffect(() => {
    async function fetchModels() {
      try {
        const response = await apiClient.listModels({ active_only: true });
        const data = response.data;
        setModels(data.items.map((m: any) => ({ id: m.id, name: m.name, model_id: m.model_id })));
        if (data.items.length > 0 && !selectedModel) {
          setSelectedModel(data.items[0].id);
        }
      } catch (err) {
        console.error('Failed to load models', err);
      }
    }
    fetchModels();
  }, [selectedModel]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModel || !prompt.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setStreamingText('');
    tokenCountRef.current = 0;

    try {
      if (stream) {
        setIsStreaming(true);
        await apiClient.streamInference(
          {
            model_id: selectedModel,
            prompt,
            temperature,
            max_tokens: maxTokens,
          },
          (token, count) => {
            tokenCountRef.current = count;
            setStreamingText((prev) => prev + token);
          },
          (doneData) => {
            setResult({
              id: `inf-${Date.now()}`,
              model_id: selectedModel,
              prompt,
              generated_text: streamingText,
              finish_reason: doneData.finish_reason,
              usage: doneData.usage,
              created_at: Date.now() / 1000,
            });
            setIsStreaming(false);
            setLoading(false);
          },
          (err) => {
            setError(err.message);
            setIsStreaming(false);
            setLoading(false);
          }
        );
      } else {
        const response = await apiClient.runInference({
          model_id: selectedModel,
          prompt,
          temperature,
          max_tokens: maxTokens,
          stream: false,
        });
        setResult(response.data);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Inference failed');
      setLoading(false);
      setIsStreaming(false);
    }
  }, [selectedModel, prompt, temperature, maxTokens, stream, streamingText]);

  const handleClear = () => {
    setPrompt('');
    setResult(null);
    setStreamingText('');
    setError(null);
  };

  const selectedModelInfo = models.find(m => m.id === selectedModel);

  return (
    <div className="inference-page">
      <div className="page-header">
        <h1 className="page-title">Inference</h1>
        <p className="page-subtitle">Run LLM inference with streaming support</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="inference-layout">
        <div className="inference-form-panel">
          <form onSubmit={handleSubmit} className="inference-form">
            <div className="form-section">
              <h3>Model Selection</h3>
              <div className="form-group">
                <label htmlFor="model">Model *</label>
                <select
                  id="model"
                  value={selectedModel || ''}
                  onChange={(e) => setSelectedModel(parseInt(e.target.value) || null)}
                  disabled={loading || isStreaming}
                  required
                >
                  <option value="">Select a model</option>
                  {models.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name} ({model.model_id})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-section">
              <h3>Prompt</h3>
              <div className="form-group">
                <textarea
                  id="prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={8}
                  placeholder="Enter your prompt here..."
                  disabled={loading || isStreaming}
                  required
                />
                <div className="char-count">{prompt.length} characters</div>
              </div>
            </div>

            <div className="form-section">
              <h3>Parameters</h3>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="temperature">
                    Temperature: {temperature.toFixed(1)}
                  </label>
                  <input
                    id="temperature"
                    type="range"
                    min={0}
                    max={2}
                    step={0.1}
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    disabled={loading || isStreaming}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="maxTokens">Max Tokens: {maxTokens}</label>
                  <input
                    id="maxTokens"
                    type="range"
                    min={1}
                    max={32768}
                    step={1}
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                    disabled={loading || isStreaming}
                  />
                </div>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={stream}
                    onChange={(e) => setStream(e.target.checked)}
                    disabled={loading || isStreaming}
                  />
                  Stream response (SSE)
                </label>
              </div>
            </div>

            <div className="form-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleClear}
                disabled={loading || isStreaming}
              >
                Clear
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || isStreaming || !selectedModel || !prompt.trim()}
              >
                {isStreaming ? 'Streaming...' : loading ? 'Running...' : stream ? 'Stream Inference' : 'Run Inference'}
              </button>
            </div>
          </form>
        </div>

        <div className="inference-result-panel">
          <div className="result-header">
            <h3>Result</h3>
            {result && (
              <div className="result-meta">
                <span className="badge badge-info">Model: {selectedModelInfo?.name}</span>
                <span className="badge badge-info">Tokens: {result.usage?.total_tokens || 0}</span>
                <span className="badge badge-info">Finish: {result.finish_reason}</span>
              </div>
            )}
          </div>

          <div className="result-content">
            {isStreaming && (
              <div className="streaming-indicator">
                <span className="pulse"></span> Streaming...
              </div>
            )}

            {result && !isStreaming && (
              <div className="result-text">
                <pre>{result.generated_text}</pre>
              </div>
            )}

            {streamingText && isStreaming && (
              <div className="result-text streaming">
                <pre>{streamingText}</pre>
                <div className="streaming-cursor"></div>
              </div>
            )}

            {!result && !isStreaming && !streamingText && (
              <div className="empty-result">
                <p>Submit a prompt to see the result here</p>
                {stream && <p className="hint">Streaming mode shows tokens in real-time</p>}
              </div>
            )}
          </div>

          {result && !isStreaming && (
            <div className="result-footer">
              <button className="btn btn-secondary btn-sm" onClick={() => navigator.clipboard.writeText(result.generated_text)}>
                Copy Result
              </button>
              <div className="usage-stats">
                <span>Prompt: {result.usage?.prompt_tokens} tokens</span>
                <span>Completion: {result.usage?.completion_tokens} tokens</span>
                <span>Total: {result.usage?.total_tokens} tokens</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Inference;
