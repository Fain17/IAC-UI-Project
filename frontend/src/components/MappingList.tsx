import React from 'react';

interface MappingListProps {
  mappings: { [key: string]: string };
  onDelete: (instance: string) => void;
}

const MappingList: React.FC<MappingListProps> = ({ mappings, onDelete }) => {
  return (
    <div>
      <h2>📋 Current Mappings</h2>
      <table>
        <thead>
          <tr><th>Instance</th><th>Launch Template</th><th>Action</th></tr>
        </thead>
        <tbody>
          {Object.entries(mappings).map(([instance, lt]) => (
            <tr key={instance}>
              <td>{instance}</td>
              <td>{lt}</td>
              <td><button onClick={() => onDelete(instance)}>🗑 Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default MappingList; 