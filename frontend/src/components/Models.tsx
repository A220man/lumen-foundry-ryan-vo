import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';

interface Model {
  id: number;
  name: string;
  model_id: string;
  description: string | null;
  max_model_len: number;
  default_temperature: number;
  default_max_tokens: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface ModelListResponse {
  items: Model[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

function Models() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ page: 1, page_size: 10, total: 0, total_pages: 0 });
  const [showForm, setShowForm] = useState(false);
  const [editingModel, setEditingModel] = useState<Model | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    model_id: '',
    description: '',
    max_model_len: 8192,
    default_temperature: 0.7,
    default_max_tokens: 512,
    is_active: true,
  });

  useEffect(() => {
    fetchModels();
  }, [pagination.page]);

  const fetchModels = async () => {
    try {
      setLoading(true);
      const response = await apiClient.listModels({
        page: pagination.page,
        page_size: pagination.page_size,
        active_only: false,
      });
      const data: ModelListResponse = response.data;
      setModels(data.items);
      setPagination({
        page: data.page,
        page_size: data.page_size,
        total: data.total,
        total_pages: data.total_pages,
      });
    } catch (err) {
      setError('Failed to load models');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingModel) {
        await apiClient.updateModel(editingModel.id, formData);
      } else {
        await apiClient.createModel(formData);
      }
      setShowForm(false);
      setEditingModel(null);
      resetForm();
      fetchModels();
    } catch (err) {
      setError('Failed to save model');
      console.error(err);
    }
  };

  const handleEdit = (model: Model) => {
    setEditingModel(model);
    setFormData({
      name: model.name,
      model_id: model.model_id,
      description: model.description || '',
      max_model_len: model.max_model_len,
      default_temperature: model.default_temperature,
      default_max_tokens: model.default_max_tokens,
      is_active: model.is_active,
    });
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this model?')) return;
    try {
      await apiClient.deleteModel(id);
      fetchModels();
    } catch (err) {
      setError('Failed to delete model');
      console.error(err);
    }
  };

  const handleNew = () => {
    setEditingModel(null);
    resetForm();
    setShowForm(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      model_id: '',
      description: '',
      max_model_len: 8192,
      default_temperature: 0.7,
      default_max_tokens: 512,
      is_active: true,
    });
  };

  const cancelForm = () => {
    setShowForm(false);
    setEditingModel(null);
    resetForm();
  };

  if (loading && models.length === 0) return <div className="loading">Loading models...</div>;

  return (
    <div className="models-page">
      <div className="page-header">
        <h1 className="page-title">Models</h1>
        <p className="page-subtitle">Manage registered LLM models</p>
        <button className="btn btn-primary" onClick={handleNew}>
          + Add Model
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {showForm && (
        <div className="modal-overlay" onClick={cancelForm}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingModel ? 'Edit Model' : 'Add Model'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="name">Name *</label>
                <input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  disabled={!!editingModel}
                />
              </div>
              <div className="form-group">
                <label htmlFor="model_id">Model ID *</label>
                <input
                  id="model_id"
                  type="text"
                  value={formData.model_id}
                  onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                  required
                  disabled={!!editingModel}
                  placeholder="e.g., meta-llama/Llama-2-7b-hf"
                />
              </div>
              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="max_model_len">Max Model Length</label>
                  <input
                    id="max_model_len"
                    type="number"
                    value={formData.max_model_len}
                    onChange={(e) => setFormData({ ...formData, max_model_len: parseInt(e.target.value) })}
                    min={1}
                    max={1048576}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="default_temperature">Default Temperature</label>
                  <input
                    id="default_temperature"
                    type="number"
                    value={formData.default_temperature}
                    onChange={(e) => setFormData({ ...formData, default_temperature: parseFloat(e.target.value) })}
                    min={0}
                    max={2}
                    step={0.1}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="default_max_tokens">Default Max Tokens</label>
                  <input
                    id="default_max_tokens"
                    type="number"
                    value={formData.default_max_tokens}
                    onChange={(e) => setFormData({ ...formData, default_max_tokens: parseInt(e.target.value) })}
                    min={1}
                    max={32768}
                  />
                </div>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  Active
                </label>
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={cancelForm}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingModel ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {models.length === 0 && !loading && (
        <div className="empty-state">
          <div className="empty-icon">🤖</div>
          <h3>No models registered</h3>
          <p>Add your first model to start running inference</p>
          <button className="btn btn-primary" onClick={handleNew}>Add Model</button>
        </div>
      )}

      {models.length > 0 && (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Model ID</th>
                <th>Max Length</th>
                <th>Temp</th>
                <th>Max Tokens</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model) => (
                <tr key={model.id}>
                  <td className="font-mono">{model.name}</td>
                  <td className="font-mono text-truncate" style={{ maxWidth: 200 }}>{model.model_id}</td>
                  <td>{model.max_model_len.toLocaleString()}</td>
                  <td>{model.default_temperature}</td>
                  <td>{model.default_max_tokens}</td>
                  <td>
                    <span className={`badge ${model.is_active ? 'badge-success' : 'badge-secondary'}`}>
                      {model.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{new Date(model.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="action-buttons-sm">
                      <button className="btn btn-ghost btn-sm" onClick={() => handleEdit(model)}>Edit</button>
                      <button className="btn btn-ghost btn-sm btn-danger" onClick={() => handleDelete(model.id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {pagination.total_pages > 1 && (
        <div className="pagination">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
            disabled={pagination.page <= 1}
          >
            Previous
          </button>
          <span className="pagination-info">
            Page {pagination.page} of {pagination.total_pages} ({pagination.total} total)
          </span>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
            disabled={pagination.page >= pagination.total_pages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default Models;
