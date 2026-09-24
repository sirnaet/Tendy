import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/client';
import { LogOut, Calendar, Clock, AlertTriangle, CheckCircle, Plus } from 'lucide-react';
import SetupModal from '../components/SetupModal';

interface Unit {
  id: string;
  name: string;
  code: string;
}

interface DashboardUnitData {
  unit: Unit;
  attended_hours: number;
  missed_hours: number;
  cancelled_hours: number;
  effective_total_hours: number;
  attendance_rate: number;
  absence_rate: number;
  allowed_absence: number;
  is_critical: boolean;
  safe_skips_left: number;
}

interface ClassLog {
  id: string;
  unit_name: string;
  unit_code: string;
  start_time: string;
  end_time: string;
  status: string;
}

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [dashboardData, setDashboardData] = useState<DashboardUnitData[]>([]);
  const [todayClasses, setTodayClasses] = useState<ClassLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSetupOpen, setIsSetupOpen] = useState(false);

  const fetchData = async () => {
    try {
      const [dashboardRes, todayRes] = await Promise.all([
        apiClient.get('/api/v1/dashboard'),
        apiClient.get('/api/v1/classes/today')
      ]);
      setDashboardData(dashboardRes.data.units || []);
      setTodayClasses(todayRes.data || []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const updateClassStatus = async (classId: string, status: string) => {
    try {
      await apiClient.put(`/api/v1/classes/${classId}/status`, { status });
      // Optimistically update
      setTodayClasses(prev => prev.map(c => c.id === classId ? { ...c, status } : c));
      // Re-fetch dashboard stats
      fetchData();
    } catch (error) {
      console.error('Failed to update status', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <header className="flex justify-between items-center glass-panel p-4 rounded-2xl">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-okay flex items-center justify-center text-white font-bold">
            {user?.email?.charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 className="font-bold text-lg">Hello, {user?.email?.split('@')[0]}</h1>
            <p className="text-textSecondary text-sm">Here's your attendance overview</p>
          </div>
        </div>
        <button onClick={logout} className="text-textSecondary hover:text-critical transition-colors p-2 bg-surface/50 rounded-lg">
          <LogOut size={20} />
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content (Left) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Calendar size={20} className="text-primary" />
              Your Courses
            </h2>
            <button 
              onClick={() => setIsSetupOpen(true)}
              className="bg-primary/10 text-primary hover:bg-primary/20 px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1 transition-colors"
            >
              <Plus size={16} /> Setup
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dashboardData.length === 0 ? (
              <div className="col-span-full text-center p-8 bg-surface/50 rounded-2xl border border-white/5">
                <p className="text-textSecondary mb-4">No courses set up yet.</p>
                <button onClick={() => setIsSetupOpen(true)} className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium">Configure Semester</button>
              </div>
            ) : (
              dashboardData.map((data) => (
                <div key={data.unit.id} className="glass-panel p-5 rounded-2xl relative overflow-hidden group">
                  {/* Status Gradient Bar */}
                  <div className={`absolute left-0 top-0 bottom-0 w-1 ${data.is_critical ? 'bg-critical' : 'bg-okay'}`} />
                  
                  <div className="flex justify-between items-start mb-4 pl-2">
                    <div>
                      <p className="text-xs font-bold text-primary tracking-wider uppercase">{data.unit.code}</p>
                      <h3 className="font-semibold text-lg">{data.unit.name}</h3>
                    </div>
                    {data.is_critical ? (
                      <span className="bg-critical/20 text-critical text-xs px-2 py-1 rounded-full font-medium flex items-center gap-1">
                        <AlertTriangle size={12} /> CRITICAL
                      </span>
                    ) : (
                      <span className="bg-okay/20 text-okay text-xs px-2 py-1 rounded-full font-medium flex items-center gap-1">
                        <CheckCircle size={12} /> OKAY
                      </span>
                    )}
                  </div>

                  <div className="space-y-4 pl-2">
                    {/* Progress Bar */}
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-textSecondary">Attendance</span>
                        <span className="font-medium">{Math.round(data.attendance_rate)}%</span>
                      </div>
                      <div className="w-full bg-surface h-2 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all duration-500 ${data.is_critical ? 'bg-critical' : 'bg-okay'}`}
                          style={{ width: `${Math.min(100, data.attendance_rate)}%` }}
                        />
                      </div>
                    </div>

                    <div className="flex justify-between items-end">
                      <div className="text-sm">
                        <p className="text-textSecondary">Absence Rate</p>
                        <p className="font-medium">{Math.round(data.absence_rate)}% / {data.allowed_absence}%</p>
                      </div>
                      
                      {/* Safe Skips Chip */}
                      <div className="bg-surface/80 border border-white/10 px-3 py-1.5 rounded-lg text-center">
                        <p className="text-xs text-textSecondary mb-0.5">Safe Skips Left</p>
                        <p className={`font-bold text-lg ${data.safe_skips_left > 0 ? 'text-okay' : 'text-critical'}`}>
                          {data.safe_skips_left}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Sidebar (Right) - Today's Classes */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Clock size={20} className="text-primary" />
            Today's Classes
          </h2>
          
          <div className="glass-panel p-4 rounded-2xl space-y-3">
            {todayClasses.length === 0 ? (
              <p className="text-textSecondary text-center py-4 text-sm">No classes scheduled for today.</p>
            ) : (
              todayClasses.map((cls) => (
                <div key={cls.id} className="bg-surface/60 border border-white/5 p-4 rounded-xl">
                  <div className="flex justify-between mb-2">
                    <span className="text-xs font-bold text-primary">{cls.unit_code}</span>
                    <span className="text-xs text-textSecondary bg-background px-2 py-0.5 rounded">
                      {cls.start_time.substring(0,5)} - {cls.end_time.substring(0,5)}
                    </span>
                  </div>
                  <h4 className="font-medium text-sm mb-3">{cls.unit_name}</h4>
                  
                  {/* Action Toggles */}
                  <div className="grid grid-cols-3 gap-2">
                    <button 
                      onClick={() => updateClassStatus(cls.id, 'Attended')}
                      className={`text-xs py-1.5 rounded-lg border transition-colors ${cls.status === 'Attended' ? 'bg-okay/20 border-okay text-okay' : 'border-white/10 text-textSecondary hover:bg-surface'}`}
                    >
                      Attended
                    </button>
                    <button 
                      onClick={() => updateClassStatus(cls.id, 'Missed')}
                      className={`text-xs py-1.5 rounded-lg border transition-colors ${cls.status === 'Missed' ? 'bg-critical/20 border-critical text-critical' : 'border-white/10 text-textSecondary hover:bg-surface'}`}
                    >
                      Missed
                    </button>
                    <button 
                      onClick={() => updateClassStatus(cls.id, 'Cancelled')}
                      className={`text-xs py-1.5 rounded-lg border transition-colors ${cls.status === 'Cancelled' ? 'bg-white/20 border-white text-white' : 'border-white/10 text-textSecondary hover:bg-surface'}`}
                    >
                      Cancelled
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
      
      <SetupModal 
        isOpen={isSetupOpen} 
        onClose={() => setIsSetupOpen(false)} 
        onSuccess={fetchData} 
      />
    </div>
  );
};

export default Dashboard;
