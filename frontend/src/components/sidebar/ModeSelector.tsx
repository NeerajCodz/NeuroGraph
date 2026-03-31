export default function ModeSelector() {
  return (
    <div className="w-full bg-slate-900 rounded-md p-1 flex">
      <button className="flex-1 rounded py-1 px-2 text-sm bg-slate-700 text-white shadow">Personal</button>
      <button className="flex-1 rounded py-1 px-2 text-sm text-slate-400 hover:text-white">Organization</button>
    </div>
  );
}

