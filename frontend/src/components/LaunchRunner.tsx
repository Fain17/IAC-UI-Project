import React, { useState } from 'react';

interface LaunchRunnerProps {
  mappings: { [key: string]: string };
  onRun: (instance: string, launch_template: string) => Promise<any>;
}

const LaunchRunner: React.FC<LaunchRunnerProps> = ({ mappings, onRun }) => {
  const [selected, setSelected] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleRun = async () => {
    const res = await onRun(selected, mappings[selected]);
    setResult(res);
  };

  return (
    <div>
      <h2>🚀 Run Launch Template Update</h2>
      <select value={selected} onChange={e => setSelected(e.target.value)}>
        <option value="">Select instance...</option>
        {Object.keys(mappings).map(name => (
          <option key={name} value={name}>{name} → {mappings[name]}</option>
        ))}
      </select>
      <button onClick={handleRun} disabled={!selected}>▶ Run</button>

      {result && (
        <div style={{ marginTop: '1em' }}>
          {result.success ? (
            <>
              ✅ AMI: <code>{result.ami_id}</code><br />
              LT: <code>{result.launch_template_id}</code><br />
              Version: <code>{result.new_version}</code>
            </>
          ) : (
            <span style={{ color: 'red' }}>❌ Error: {result.error}</span>
          )}
        </div>
      )}
    </div>
  );
};

export default LaunchRunner; 