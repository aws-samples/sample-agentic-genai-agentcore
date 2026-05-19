import { OutputPanel } from './OutputPanel';
import { FileUpload } from './FileUpload';

export function MainWorkspace() {
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Compact Header */}
      <header className="bg-white shadow-sm border-b flex-shrink-0">
        <div className="px-6 py-3">
          <h1 className="text-xl font-bold text-gray-900">
            Campaign Review System
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-4 overflow-hidden">
        <div className="grid grid-cols-2 gap-4 h-full">
          {/* Upload Panel - Left Side */}
          <FileUpload />
          
          {/* Output Panel - Right Side */}
          <OutputPanel />
        </div>
      </main>
    </div>
  );
}
