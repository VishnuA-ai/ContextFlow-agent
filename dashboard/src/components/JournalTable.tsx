import { ScrollText } from 'lucide-react';
import type { JournalEntry } from '../types';

interface JournalTableProps {
  entries: JournalEntry[];
}

export function JournalTable({ entries }: JournalTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700/50">
            <th className="text-left py-3 px-4 font-semibold text-gray-300">Seq</th>
            <th className="text-left py-3 px-4 font-semibold text-gray-300">Action</th>
            <th className="text-left py-3 px-4 font-semibold text-gray-300">Hash Change</th>
            <th className="text-left py-3 px-4 font-semibold text-gray-300">Time</th>
          </tr>
        </thead>
        <tbody>
          {entries.length === 0 ? (
            <tr>
              <td colSpan={4} className="text-center py-8 text-gray-400">
                No journal entries yet
              </td>
            </tr>
          ) : (
            entries.map((entry, index) => (
              <tr 
                key={entry.sequence} 
                className="border-b border-gray-700/30 hover:bg-gray-700/20 animate-slide-in"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <td className="py-3 px-4 font-mono text-gray-400">{entry.sequence}</td>
                <td className="py-3 px-4 text-white">{entry.action}</td>
                <td className="py-3 px-4 font-mono text-xs text-gray-400">{entry.hash_change}</td>
                <td className="py-3 px-4 text-gray-400">
                  {new Date(entry.timestamp * 1000).toLocaleTimeString()}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
