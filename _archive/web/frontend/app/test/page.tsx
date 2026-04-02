'use client';

export default function TestPage() {
  return (
    <div className="min-h-screen bg-black text-white p-8">
      <h1 className="text-4xl mb-4">Test Page - Dashboard Content Check</h1>
      
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-500 p-4 rounded">
          <h2>Sidebar Area</h2>
          <p>This represents the sidebar</p>
        </div>
        
        <div className="bg-green-500 p-4 rounded">
          <h2>Main Content Area</h2>
          <p>This is where the charts should appear</p>
          <div className="mt-4 bg-white/20 p-4 rounded">
            <p>Chart 1</p>
          </div>
          <div className="mt-4 bg-white/20 p-4 rounded">
            <p>Chart 2</p>
          </div>
        </div>
        
        <div className="bg-red-500 p-4 rounded">
          <h2>Live Activity</h2>
          <p>This represents the right sidebar</p>
        </div>
      </div>
    </div>
  );
}