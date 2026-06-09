import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';

import Dashboard from './pages/Dashboard';

// Placeholder components for pages until we build them
const Jobs = () => <div><h1>Jobs</h1><p>List of all jobs will go here.</p></div>;
const CreateJob = () => <div><h1>Create Job</h1><p>Form to create a job will go here.</p></div>;
const DLQ = () => <div><h1>Dead Letter Queue</h1><p>Failed jobs will go here.</p></div>;

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="jobs" element={<Jobs />} />
        <Route path="create" element={<CreateJob />} />
        <Route path="dlq" element={<DLQ />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
