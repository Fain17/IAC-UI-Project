import React, { useState } from 'react';

interface AddMappingFormProps {
  onCreate: (instance: string, lt: string) => void;
}

const AddMappingForm: React.FC<AddMappingFormProps> = ({ onCreate }) => {
  const [instance, setInstance] = useState('');
  const [lt, setLt] = useState('');

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onCreate(instance, lt);
    setInstance('');
    setLt('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>➕ Add New Mapping</h2>
      <input value={instance} onChange={e => setInstance(e.target.value)} placeholder="Instance Tag" required />
      <input value={lt} onChange={e => setLt(e.target.value)} placeholder="Launch Template" required />
      <button type="submit">💾 Save</button>
    </form>
  );
};

export default AddMappingForm; 