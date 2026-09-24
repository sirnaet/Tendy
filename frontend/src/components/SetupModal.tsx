import React, { useState } from 'react';
import { X, Plus } from 'lucide-react';
import apiClient from '../api/client';

interface SetupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const SetupModal: React.FC<SetupModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [allowedAbsence, setAllowedAbsence] = useState(20);
  const [units, setUnits] = useState([{ name: '', code: '', slots: [{ day_of_week: 1, start_time: '09:00', end_time: '10:00' }] }]);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleAddUnit = () => {
    setUnits([...units, { name: '', code: '', slots: [{ day_of_week: 1, start_time: '09:00', end_time: '10:00' }] }]);
  };

  const handleAddSlot = (unitIndex: number) => {
    const newUnits = [...units];
    newUnits[unitIndex].slots.push({ day_of_week: 1, start_time: '09:00', end_time: '10:00' });
    setUnits(newUnits);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        semester: {
          start_date: startDate,
          end_date: endDate,
          holidays: [], // Simplification for MVP
          allowed_absence_percent: allowedAbsence
        },
        units: units.map(u => ({
          ...u,
          slots: u.slots.map(s => ({
            ...s,
            day_of_week: Number(s.day_of_week)
          }))
        }))
      };
      
      await apiClient.post('/api/v1/semesters/generate', payload);
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Failed to setup semester', error);
      alert('Failed to setup semester. Check console.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="glass-panel w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-textSecondary hover:text-white">
          <X size={24} />
        </button>
        
        <h2 className="text-2xl font-bold mb-6">Setup Semester</h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-textSecondary mb-1">Start Date</label>
              <input type="date" required value={startDate} onChange={e => setStartDate(e.target.value)} className="w-full bg-surface/50 border border-white/10 rounded p-2 focus:outline-none focus:border-primary" />
            </div>
            <div>
              <label className="block text-sm text-textSecondary mb-1">End Date</label>
              <input type="date" required value={endDate} onChange={e => setEndDate(e.target.value)} className="w-full bg-surface/50 border border-white/10 rounded p-2 focus:outline-none focus:border-primary" />
            </div>
          </div>
          
          <div>
            <label className="block text-sm text-textSecondary mb-1">Allowed Absence %</label>
            <input type="number" min="0" max="100" required value={allowedAbsence} onChange={e => setAllowedAbsence(Number(e.target.value))} className="w-full bg-surface/50 border border-white/10 rounded p-2 focus:outline-none focus:border-primary" />
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold">Units</h3>
              <button type="button" onClick={handleAddUnit} className="text-sm flex items-center gap-1 text-primary hover:text-primary/80">
                <Plus size={16} /> Add Unit
              </button>
            </div>
            
            {units.map((unit, uIdx) => (
              <div key={uIdx} className="p-4 border border-white/10 rounded-xl bg-surface/30 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <input placeholder="Unit Code (e.g. CS101)" required value={unit.code} onChange={e => {
                    const nu = [...units]; nu[uIdx].code = e.target.value; setUnits(nu);
                  }} className="bg-surface/50 border border-white/10 rounded p-2 text-sm focus:outline-none focus:border-primary" />
                  <input placeholder="Unit Name" required value={unit.name} onChange={e => {
                    const nu = [...units]; nu[uIdx].name = e.target.value; setUnits(nu);
                  }} className="bg-surface/50 border border-white/10 rounded p-2 text-sm focus:outline-none focus:border-primary" />
                </div>
                
                <div className="space-y-2 pl-4 border-l-2 border-white/10">
                  {unit.slots.map((slot, sIdx) => (
                    <div key={sIdx} className="flex items-center gap-2">
                      <select value={slot.day_of_week} onChange={e => {
                        const nu = [...units]; nu[uIdx].slots[sIdx].day_of_week = Number(e.target.value); setUnits(nu);
                      }} className="bg-surface/50 border border-white/10 rounded p-1.5 text-sm">
                        <option value={1}>Mon</option><option value={2}>Tue</option><option value={3}>Wed</option>
                        <option value={4}>Thu</option><option value={5}>Fri</option><option value={6}>Sat</option><option value={7}>Sun</option>
                      </select>
                      <input type="time" required value={slot.start_time} onChange={e => {
                        const nu = [...units]; nu[uIdx].slots[sIdx].start_time = e.target.value; setUnits(nu);
                      }} className="bg-surface/50 border border-white/10 rounded p-1.5 text-sm" />
                      <span>-</span>
                      <input type="time" required value={slot.end_time} onChange={e => {
                        const nu = [...units]; nu[uIdx].slots[sIdx].end_time = e.target.value; setUnits(nu);
                      }} className="bg-surface/50 border border-white/10 rounded p-1.5 text-sm" />
                    </div>
                  ))}
                  <button type="button" onClick={() => handleAddSlot(uIdx)} className="text-xs text-textSecondary hover:text-white flex items-center gap-1 mt-2">
                    <Plus size={14} /> Add Slot
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button type="submit" disabled={loading} className="w-full bg-primary hover:bg-primary/90 text-white font-medium py-3 rounded-xl transition-colors">
            {loading ? 'Generating...' : 'Save & Generate Schedule'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default SetupModal;
