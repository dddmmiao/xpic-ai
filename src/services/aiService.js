/**
 * AI Service — 连接后端进行真实分析 (BiomedCLIP + Qwen VL 双层架构)
 */
const API_BASE = import.meta.env.VITE_API_BASE || '';
const API_URL = `${API_BASE}/predict`;
const TIMEOUT_MS = 60000; // 60s — BiomedCLIP 本地 1-2s，Qwen API 约 5-10s

/**
 * @param {File} file
 * @returns {Promise<Object>}
 */
export const analyzeImage = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
        const res = await fetch(API_URL, {
            method: 'POST',
            body: formData,
            signal: controller.signal,
        });
        clearTimeout(timer);

        if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            throw new Error(body.error || `服务器错误 (${res.status})`);
        }

        return await res.json();
    } catch (err) {
        clearTimeout(timer);

        if (err.name === 'AbortError') {
            throw new Error('分析超时，请检查后端状态。');
        }
        if (err.message === 'Failed to fetch') {
            throw new Error('无法连接到 AI 后端服务，请确认后端已启动。');
        }
        throw err;
    }
};
