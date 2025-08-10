// components/features/MaskCreator/MaskCreator.jsx
import { useState, useRef, useCallback } from 'react';
import { apiService } from '../../../services/apiService';

export const MaskCreator = () => {
  const canvasRef = useRef(null);
  const [image, setImage] = useState(null);
  const [masks, setMasks] = useState([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawMode, setDrawMode] = useState('point'); // 'point' or 'rectangle'

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = canvasRef.current;
          const ctx = canvas.getContext('2d');
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);
          setImage(img);
        };
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
    }
  };

  const handleCanvasClick = useCallback((event) => {
    if (!image) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    if (drawMode === 'point') {
      const newMask = { type: 'point', x, y, id: Date.now() };
      setMasks(prev => [...prev, newMask]);
      
      // Draw point on canvas
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = 'rgba(255, 0, 0, 0.7)';
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, 2 * Math.PI);
      ctx.fill();
    }
  }, [image, drawMode]);

  const saveMasks = async () => {
    if (masks.length === 0) return;

    try {
      const canvas = canvasRef.current;
      const imageData = canvas.toDataURL();
      
      await apiService.saveMaskData({
        image_data: imageData,
        masks: masks,
        timestamp: new Date().toISOString()
      });

      alert('Masks saved successfully!');
    } catch (error) {
      console.error('Failed to save masks:', error);
      alert('Failed to save masks');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Mask Creator</h2>
      
      <div className="mb-4">
        <input
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          className="mb-4"
        />
        
        <div className="flex gap-4 mb-4">
          <button
            onClick={() => setDrawMode('point')}
            className={`px-4 py-2 rounded ${
              drawMode === 'point' 
                ? 'bg-primary text-white' 
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            Point Mode
          </button>
          <button
            onClick={() => setDrawMode('rectangle')}
            className={`px-4 py-2 rounded ${
              drawMode === 'rectangle' 
                ? 'bg-primary text-white' 
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            Rectangle Mode
          </button>
        </div>
      </div>

      <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
        <canvas
          ref={canvasRef}
          onClick={handleCanvasClick}
          className="max-w-full h-auto cursor-crosshair"
          style={{ maxHeight: '500px' }}
        />
      </div>

      <div className="mt-4 flex gap-4">
        <button
          onClick={() => setMasks([])}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          Clear Masks
        </button>
        <button
          onClick={saveMasks}
          disabled={masks.length === 0}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
        >
          Save Masks ({masks.length})
        </button>
      </div>
    </div>
  );
};